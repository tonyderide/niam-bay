import { Component, EventEmitter, Input, Output, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Recipe, RecipeStep } from '../../models/recipe.model';

interface StepState {
  step: RecipeStep;
  completed: boolean;
  timerRunning: boolean;
  timerSeconds: number;
  intervalId: any;
}

@Component({
  selector: 'app-recipe-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './recipe-detail.component.html',
  styleUrl: './recipe-detail.component.scss'
})
export class RecipeDetailComponent implements OnDestroy {
  @Input() recipe!: Recipe;
  @Output() close = new EventEmitter<void>();

  stepStates: StepState[] = [];
  private audioContext: AudioContext | null = null;

  ngOnChanges(): void {
    if (this.recipe) {
      this.stepStates = this.recipe.steps.map(step => ({
        step,
        completed: false,
        timerRunning: false,
        timerSeconds: (step.timerMinutes || 0) * 60,
        intervalId: null,
      }));
    }
  }

  ngOnDestroy(): void {
    this.stepStates.forEach(s => {
      if (s.intervalId) clearInterval(s.intervalId);
    });
  }

  toggleStep(index: number): void {
    const state = this.stepStates[index];
    state.completed = !state.completed;
    if (state.completed && state.intervalId) {
      clearInterval(state.intervalId);
      state.timerRunning = false;
    }
  }

  startTimer(index: number): void {
    const state = this.stepStates[index];
    if (state.timerRunning || state.timerSeconds <= 0) return;

    state.timerRunning = true;
    state.intervalId = setInterval(() => {
      state.timerSeconds--;
      if (state.timerSeconds <= 0) {
        clearInterval(state.intervalId);
        state.timerRunning = false;
        state.intervalId = null;
        this.playAlarm();
      }
    }, 1000);
  }

  pauseTimer(index: number): void {
    const state = this.stepStates[index];
    if (state.intervalId) {
      clearInterval(state.intervalId);
      state.intervalId = null;
    }
    state.timerRunning = false;
  }

  resetTimer(index: number): void {
    const state = this.stepStates[index];
    if (state.intervalId) {
      clearInterval(state.intervalId);
      state.intervalId = null;
    }
    state.timerRunning = false;
    state.timerSeconds = (state.step.timerMinutes || 0) * 60;
  }

  formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  get activeStepIndex(): number {
    return this.stepStates.findIndex(s => !s.completed);
  }

  private playAlarm(): void {
    try {
      if (!this.audioContext) {
        this.audioContext = new AudioContext();
      }
      const ctx = this.audioContext;
      // Play 3 beeps
      for (let i = 0; i < 3; i++) {
        const oscillator = ctx.createOscillator();
        const gain = ctx.createGain();
        oscillator.connect(gain);
        gain.connect(ctx.destination);
        oscillator.frequency.value = 880;
        oscillator.type = 'sine';
        gain.gain.value = 0.3;
        const startTime = ctx.currentTime + i * 0.3;
        oscillator.start(startTime);
        oscillator.stop(startTime + 0.2);
      }
    } catch {
      // Audio not available
    }
  }

  onClose(): void {
    this.close.emit();
  }

  onOverlayClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('overlay')) {
      this.onClose();
    }
  }
}
