// @vitest-environment happy-dom

import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import VideoFrameSource from './VideoFrameSource';

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function fakeStream() {
  const stop = vi.fn();
  const stream = new MediaStream();
  const track = Object.assign(new EventTarget(), { stop });
  Object.defineProperty(stream, 'getTracks', { value: () => [track] });
  return { stream, stop, track };
}

describe('video camera lifecycle', () => {
  let host: HTMLDivElement;
  let root: Root;
  let getUserMedia: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
    vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
    vi.stubGlobal('requestAnimationFrame', vi.fn(() => 1));
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
    getUserMedia = vi.fn();
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
    vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    host = document.createElement('div');
    document.body.append(host);
    root = createRoot(host);
  });

  afterEach(async () => {
    await act(async () => { root.unmount(); });
    host.remove();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  async function render(deviceId: string | null = null, sourceMode: 'camera' | 'file' = 'camera', extra: {
    videoUrl?: string;
    onReadyChange?: (ready: boolean) => void;
  } = {}) {
    await act(async () => { root.render(React.createElement(VideoFrameSource, { sourceMode, deviceId, ...extra })); });
  }

  it('shows a recoverable error instead of a permanently blank panel when camera startup never resolves', async () => {
    getUserMedia.mockReturnValue(new Promise(() => {}));
    await render();
    await act(async () => { await vi.advanceTimersByTimeAsync(15_000); });
    expect(host.textContent).toContain('Camera Not Responding');
    expect(host.querySelector('button')?.textContent).toContain('Retry Camera');
  });

  it('does not hide a working new camera when an old request rejects after switching cameras', async () => {
    const oldRequest = deferred<MediaStream>();
    const newRequest = deferred<MediaStream>();
    const active = fakeStream();
    getUserMedia.mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(newRequest.promise);
    await render('old');
    await render('new');
    await act(async () => { newRequest.resolve(active.stream); });
    expect(vi.mocked(console.error).mock.calls).toEqual([]);
    await act(async () => { oldRequest.reject(new DOMException('denied', 'NotAllowedError')); });
    expect(host.querySelector('video')?.srcObject).toBe(active.stream);
    expect(host.textContent).not.toContain('Permission Denied');
    expect(getUserMedia).toHaveBeenCalledTimes(2);
  });

  it('stops only the stale stream and still releases the active stream on a source switch', async () => {
    const oldRequest = deferred<MediaStream>();
    const newRequest = deferred<MediaStream>();
    const stale = fakeStream();
    const active = fakeStream();
    getUserMedia.mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(newRequest.promise);
    await render('old');
    await render('new');
    await act(async () => { newRequest.resolve(active.stream); });
    await act(async () => { oldRequest.resolve(stale.stream); });
    expect(stale.stop).toHaveBeenCalledOnce();
    expect(active.stop).not.toHaveBeenCalled();
    await render(null, 'file');
    expect(active.stop).toHaveBeenCalledOnce();
  });

  it('keeps video and canvas mounted after an error so retry can attach a stream', async () => {
    getUserMedia.mockRejectedValue(new DOMException('denied', 'NotAllowedError'));
    await render();
    expect(host.textContent).toContain('Permission Denied');
    expect(host.querySelector('video')).not.toBeNull();
    expect(host.querySelector('canvas')).not.toBeNull();
  });

  it('does not treat stale file frames as a ready camera while camera acquisition is pending', async () => {
    const onReadyChange = vi.fn();
    getUserMedia.mockReturnValue(new Promise(() => {}));
    await render(null, 'file', { videoUrl: 'blob:recorded-test', onReadyChange });
    await render(null, 'camera', { onReadyChange });
    const video = host.querySelector('video');
    if (!video) throw new Error('Missing video element');
    await act(async () => { video.dispatchEvent(new Event('loadeddata')); });
    expect(onReadyChange).not.toHaveBeenCalledWith(true);
    expect(video.getAttribute('src')).toBeNull();
  });

  it('releases a stream which arrives after the startup timeout', async () => {
    const request = deferred<MediaStream>();
    const late = fakeStream();
    getUserMedia.mockReturnValue(request.promise);
    await render();
    await act(async () => { await vi.advanceTimersByTimeAsync(15_000); });
    await act(async () => { request.resolve(late.stream); });
    expect(late.stop).toHaveBeenCalledOnce();
    expect(host.querySelector('video')?.srcObject).toBeNull();
  });

  it('retries a failed connection in place and reports readiness only after frames load', async () => {
    const active = fakeStream();
    const onReadyChange = vi.fn();
    getUserMedia.mockRejectedValueOnce(new DOMException('denied', 'NotAllowedError'))
      .mockResolvedValueOnce(active.stream);
    await render(null, 'camera', { onReadyChange });
    const retry = host.querySelector('button');
    if (!retry) throw new Error('Missing retry button');
    await act(async () => { retry.click(); });
    const video = host.querySelector('video');
    if (!video) throw new Error('Missing video element');
    expect(video.srcObject).toBe(active.stream);
    expect(host.textContent).not.toContain('Permission Denied');
    expect(onReadyChange).not.toHaveBeenCalledWith(true);
    await act(async () => { video.dispatchEvent(new Event('loadeddata')); });
    expect(onReadyChange).toHaveBeenLastCalledWith(true);
    await act(async () => { active.track.dispatchEvent(new Event('ended')); });
    expect(host.textContent).toContain('Camera Disconnected');
    expect(onReadyChange).toHaveBeenLastCalledWith(false);
  });

  it('does not restart the camera when parent readiness callbacks change', async () => {
    const active = fakeStream();
    getUserMedia.mockResolvedValue(active.stream);
    await render(null, 'camera', { onReadyChange: vi.fn() });
    await render(null, 'camera', { onReadyChange: vi.fn() });
    expect(getUserMedia).toHaveBeenCalledOnce();
    expect(active.stop).not.toHaveBeenCalled();
  });
});
