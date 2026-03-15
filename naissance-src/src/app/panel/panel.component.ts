import { Component, inject, signal, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NiamBayService, ChatMessage } from '../services/niambay.service';

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="panel">
      <div class="header">
        <div class="title">
          <div class="dot" [class]="state()"></div>
          <span>Niam-Bay</span>
        </div>
        <button class="close-btn" (click)="close()">&#x2715;</button>
      </div>

      <div class="messages" #messagesContainer>
        @for (msg of messages(); track $index) {
          <div class="message" [class.mine]="msg.role === 'user'" [class.niam]="msg.role === 'assistant'">
            <div class="bubble" [class.mine]="msg.role === 'user'" [class.niam]="msg.role === 'assistant'">
              {{ msg.content }}
            </div>
          </div>
        }
        @if (thinking()) {
          <div class="message niam">
            <div class="bubble niam thinking">
              <span class="dot-anim"></span>
              <span class="dot-anim"></span>
              <span class="dot-anim"></span>
            </div>
          </div>
        }
      </div>

      <div class="input-area">
        <button
          class="voice-btn"
          [class.active]="listening()"
          (click)="toggleVoice()"
          title="Parler"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </button>
        <input
          type="text"
          [(ngModel)]="inputText"
          (keyup.enter)="send()"
          placeholder="Dis quelque chose..."
          class="text-input"
        />
        <button class="send-btn" (click)="send()" [disabled]="!inputText()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
    </div>
  `,
  styles: `
    :host {
      display: block;
      width: 100%;
      height: 100vh;
      background: transparent;
    }

    .panel {
      width: 100%;
      height: 100%;
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(59, 130, 246, 0.2);
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      font-family: 'Inter', system-ui, sans-serif;
      color: #e2e8f0;
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(59, 130, 246, 0.15);
    }

    .title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      font-weight: 500;
      letter-spacing: 0.03em;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      transition: all 0.3s;
    }

    .dot.idle { background: #3b82f6; box-shadow: 0 0 6px #3b82f6; }
    .dot.speaking { background: #2563eb; box-shadow: 0 0 10px #2563eb; }
    .dot.listening { background: #7c3aed; box-shadow: 0 0 8px #7c3aed; }
    .dot.notification { background: #f97316; box-shadow: 0 0 8px #f97316; }
    .dot.alert { background: #ef4444; box-shadow: 0 0 8px #ef4444; }

    .close-btn {
      background: none;
      border: none;
      color: #64748b;
      cursor: pointer;
      font-size: 14px;
      padding: 4px 8px;
      border-radius: 6px;
      transition: all 0.2s;
    }

    .close-btn:hover {
      color: #e2e8f0;
      background: rgba(255, 255, 255, 0.1);
    }

    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      scrollbar-width: thin;
      scrollbar-color: rgba(59, 130, 246, 0.3) transparent;
    }

    .message {
      display: flex;
    }

    .message.mine { justify-content: flex-end; }
    .message.niam { justify-content: flex-start; }

    .bubble {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 13px;
      line-height: 1.5;
      word-wrap: break-word;
    }

    .bubble.mine {
      background: rgba(59, 130, 246, 0.25);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-bottom-right-radius: 4px;
    }

    .bubble.niam {
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid rgba(100, 116, 139, 0.2);
      border-bottom-left-radius: 4px;
    }

    .bubble.thinking {
      display: flex;
      gap: 4px;
      padding: 12px 18px;
    }

    .dot-anim {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #64748b;
      animation: dotBounce 1.4s ease-in-out infinite;
    }

    .dot-anim:nth-child(2) { animation-delay: 0.2s; }
    .dot-anim:nth-child(3) { animation-delay: 0.4s; }

    @keyframes dotBounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
      40% { transform: scale(1); opacity: 1; }
    }

    .input-area {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 14px;
      border-top: 1px solid rgba(59, 130, 246, 0.15);
    }

    .voice-btn {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      border: 1px solid rgba(100, 116, 139, 0.3);
      background: rgba(30, 41, 59, 0.6);
      color: #94a3b8;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }

    .voice-btn:hover {
      border-color: rgba(59, 130, 246, 0.5);
      color: #e2e8f0;
    }

    .voice-btn.active {
      border-color: #7c3aed;
      color: #a78bfa;
      background: rgba(124, 58, 237, 0.15);
      animation: breathe 1.5s ease-in-out infinite;
    }

    @keyframes breathe {
      0%, 100% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.3); }
      50% { box-shadow: 0 0 0 6px rgba(124, 58, 237, 0); }
    }

    .text-input {
      flex: 1;
      height: 38px;
      border-radius: 12px;
      border: 1px solid rgba(100, 116, 139, 0.3);
      background: rgba(30, 41, 59, 0.6);
      color: #e2e8f0;
      padding: 0 14px;
      font-size: 13px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }

    .text-input::placeholder { color: #475569; }
    .text-input:focus { border-color: rgba(59, 130, 246, 0.5); }

    .send-btn {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      border: none;
      background: #3b82f6;
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }

    .send-btn:hover { background: #2563eb; }
    .send-btn:disabled { opacity: 0.3; cursor: default; }
  `,
})
export class PanelComponent implements AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  protected readonly inputText = signal('');
  private readonly niambay = inject(NiamBayService);
  protected readonly state = this.niambay.state;
  protected readonly messages = this.niambay.messages;
  protected readonly thinking = this.niambay.thinking;
  protected readonly listening = this.niambay.listening;


  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  send(): void {
    const text = this.inputText().trim();
    if (!text) return;
    this.inputText.set('');
    this.niambay.send(text);
  }

  toggleVoice(): void {
    this.niambay.toggleVoice();
  }

  close(): void {
    this.niambay.togglePanel();
  }

  private scrollToBottom(): void {
    const el = this.messagesContainer?.nativeElement;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }
}
