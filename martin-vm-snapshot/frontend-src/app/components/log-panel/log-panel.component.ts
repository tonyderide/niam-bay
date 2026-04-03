import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { LogEntry } from '../../models/log-entry.model';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-log-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="log-panel" [class.minimized]="minimized">
      <div class="log-header" (click)="minimized = !minimized">
        <div class="log-title">
          <span class="log-icon">&#9611;</span>
          SYSTEM LOG
          <span class="log-count">[{{ logs.length }}]</span>
        </div>
        <div class="log-controls" (click)="$event.stopPropagation()">
          <select [(ngModel)]="levelFilter" class="level-filter">
            <option value="ALL">ALL</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
          <button class="log-btn" (click)="togglePause()">
            {{ paused ? '▶ RESUME' : '⏸ PAUSE' }}
          </button>
          <button class="log-btn" (click)="clearLogs()">CLEAR</button>
          <button class="log-btn minimize-btn" (click)="minimized = !minimized">
            {{ minimized ? '▲' : '▼' }}
          </button>
        </div>
      </div>
      @if (!minimized) {
        <div class="log-body" #logBody>
          @for (log of filteredLogs(); track $index) {
            <div class="log-line" [class]="'level-' + log.level.toLowerCase()">
              <span class="log-ts">{{ log.ts }}</span>
              <span class="log-level">{{ log.level }}</span>
              <span class="log-logger">{{ log.logger }}</span>
              <span class="log-msg">{{ log.msg }}</span>
            </div>
          }
          @if (filteredLogs().length === 0) {
            <div class="log-empty">Waiting for logs...</div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .log-panel {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 220px;
      background: var(--bg-deep);
      border-top: 1px solid var(--border-dim);
      display: flex;
      flex-direction: column;
      z-index: 200;
      font-family: var(--font-mono);

      &.minimized {
        height: auto;
      }
    }

    .log-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 16px;
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border-dim);
      cursor: pointer;
      user-select: none;
      min-height: 34px;
    }

    .log-title {
      font-size: 0.75rem;
      color: var(--neon-cyan);
      letter-spacing: 2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .log-icon {
      color: var(--neon-green);
      animation: blink-dot 1.5s infinite;
    }

    .log-count {
      color: var(--color-muted);
      font-size: 0.7rem;
    }

    .log-controls {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .level-filter {
      padding: 3px 8px;
      background: var(--bg-deep);
      border: 1px solid var(--border-dim);
      border-radius: 2px;
      color: var(--color-text);
      font-size: 0.7rem;
      font-family: var(--font-mono);

      &:focus {
        outline: none;
        border-color: var(--neon-cyan);
      }
    }

    .log-btn {
      padding: 3px 10px;
      background: transparent;
      border: 1px solid var(--border-dim);
      border-radius: 2px;
      color: var(--color-muted);
      font-size: 0.7rem;
      font-family: var(--font-mono);
      cursor: pointer;
      letter-spacing: 1px;
      transition: all 0.2s;

      &:hover {
        color: var(--neon-cyan);
        border-color: var(--neon-cyan);
      }
    }

    .minimize-btn {
      min-width: 28px;
      text-align: center;
    }

    .log-body {
      flex: 1;
      overflow-y: auto;
      padding: 4px 0;
    }

    .log-line {
      display: flex;
      gap: 10px;
      padding: 2px 16px;
      font-size: 0.75rem;
      line-height: 1.6;
      white-space: nowrap;

      &:hover {
        background: rgba(0, 255, 249, 0.03);
      }

      &.level-info .log-level { color: var(--neon-cyan); }
      &.level-warn .log-level { color: var(--neon-amber); }
      &.level-error .log-level { color: var(--color-danger); }
      &.level-error { background: rgba(255, 51, 102, 0.05); }
      &.level-debug .log-level { color: var(--color-muted); }
      &.level-debug .log-msg { color: var(--color-muted); }
    }

    .log-ts {
      color: var(--color-muted);
      min-width: 85px;
    }

    .log-level {
      min-width: 45px;
      font-weight: 600;
    }

    .log-logger {
      color: var(--neon-magenta);
      min-width: 140px;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .log-msg {
      color: var(--color-text);
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .log-empty {
      text-align: center;
      color: var(--color-muted);
      padding: 2rem;
      font-size: 0.8rem;
      letter-spacing: 2px;
    }
  `]
})
export class LogPanelComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('logBody') logBody?: ElementRef<HTMLDivElement>;

  logs: LogEntry[] = [];
  paused = false;
  minimized = window.innerWidth < 768;
  levelFilter = 'ALL';
  private sub?: Subscription;
  private shouldScroll = true;
  private maxLogs = 500;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.connectLogs();
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll && !this.paused && this.logBody) {
      const el = this.logBody.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }

  private connectLogs(): void {
    this.sub = this.api.streamLogs().subscribe({
      next: (entry) => {
        if (!this.paused) {
          this.logs.push(entry);
          if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
          }
          this.shouldScroll = true;
        }
      },
      error: () => {
        setTimeout(() => this.connectLogs(), 3000);
      }
    });
  }

  filteredLogs(): LogEntry[] {
    if (this.levelFilter === 'ALL') return this.logs;
    return this.logs.filter(l => l.level === this.levelFilter);
  }

  togglePause(): void {
    this.paused = !this.paused;
    if (!this.paused) {
      this.shouldScroll = true;
    }
  }

  clearLogs(): void {
    this.logs = [];
  }
}
