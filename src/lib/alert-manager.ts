"use client";

export class AlertManager {
  private lastAlertTime: number = 0;
  private cooldownMs: number;
  private audioContext: AudioContext | null = null;
  private audioUnlocked: boolean = false;

  constructor(cooldownSeconds: number = 5) {
    this.cooldownMs = cooldownSeconds * 1000;
  }

  setCooldown(seconds: number) {
    this.cooldownMs = seconds * 1000;
  }

  async unlockAudio(): Promise<void> {
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
        console.log('[ALERT] Audio context resumed');
      }
      
      // Test with a very short beep to unlock audio
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = 800;
      gain.gain.value = 0.001; // Very quiet test beep
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start();
      osc.stop(this.audioContext.currentTime + 0.01);
      
      this.audioUnlocked = true;
      console.log('[ALERT] Audio unlocked and tested');
    } catch (e) {
      console.warn('[ALERT] Failed to unlock audio:', e);
    }
  }

  async trigger(isAudioEnabled: boolean = true): Promise<boolean> {
    const now = Date.now();
    
    // Check cooldown
    if (now - this.lastAlertTime < this.cooldownMs) {
      return false;
    }
    
    this.lastAlertTime = now;
    console.log('[ALERT] Zone breach detected! Audio enabled:', isAudioEnabled);
    
    // Only play sound if audio is enabled
    if (isAudioEnabled) {
      await this.playAlertSound();
    }
    
    return true;
  }

  private async playAlertSound(): Promise<void> {
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      // Resume if suspended
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      const ctx = this.audioContext;
      
      // Create a loud, attention-grabbing alarm: 3 quick beeps
      for (let i = 0; i < 3; i++) {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        const startTime = ctx.currentTime + (i * 0.15);
        
        osc.type = 'square'; // Harsher tone
        osc.frequency.setValueAtTime(1000, startTime);
        
        gain.gain.setValueAtTime(0.4, startTime); // Louder
        gain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.1);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(startTime);
        osc.stop(startTime + 0.1);
      }
      
      console.log('[ALERT] Sound played successfully');
    } catch (e) {
      console.error('[ALERT] Failed to play audio:', e);
    }
  }
}
