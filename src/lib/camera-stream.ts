export function requestCameraStream(
  constraints: MediaStreamConstraints,
  signal: AbortSignal,
  timeoutMs = 12_000,
): Promise<MediaStream> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const cleanup = () => {
      clearTimeout(timer);
      signal.removeEventListener('abort', abort);
    };
    const fail = (error: unknown) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(error);
    };
    const abort = () => fail(new DOMException('Camera request cancelled', 'AbortError'));
    const timer = setTimeout(() => {
      fail(new DOMException('Camera startup timed out', 'TimeoutError'));
    }, timeoutMs);
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) { abort(); return; }

    // Browsers cannot cancel getUserMedia; release any stream arriving after cancellation.
    try {
      navigator.mediaDevices.getUserMedia(constraints).then(stream => {
        if (settled || signal.aborted) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        settled = true;
        cleanup();
        resolve(stream);
      }, fail);
    } catch (error) {
      fail(error);
    }
  });
}
