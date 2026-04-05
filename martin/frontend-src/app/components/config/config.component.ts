import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { BotConfig } from '../../models/config.model';

@Component({
  selector: 'app-config',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './config.component.html',
  styleUrl: './config.component.scss'
})
export class ConfigComponent implements OnInit {
  configForm!: FormGroup;
  configs: BotConfig[] = [];
  saveMessage = '';
  saveError = false;
  editingId: number | null = null;

  instruments = ['PF_XBTUSD', 'PF_ETHUSD'];
  strategies = ['RSI_EMA', 'MANUAL'];

  constructor(private fb: FormBuilder, private api: ApiService) {}

  ngOnInit(): void {
    this.configForm = this.fb.group({
      instrument: ['PF_XBTUSD', Validators.required],
      initialStake: [5, [Validators.required, Validators.min(1)]],
      maxDoublings: [3, [Validators.required, Validators.min(1), Validators.max(10)]],
      takeProfitPct: [1.5, [Validators.required, Validators.min(0.1)]],
      stopLossPct: [1.0, [Validators.required, Validators.min(0.1)]],
      leverage: [2, [Validators.required, Validators.min(1), Validators.max(10)]],
      signalStrategy: ['RSI_EMA', Validators.required],
      active: [true],
      demo: [false]
    });

    this.loadConfigs();
  }

  loadConfigs(): void {
    this.api.getConfigs().subscribe(configs => this.configs = configs);
  }

  onSubmit(): void {
    if (this.configForm.valid) {
      const config: BotConfig = { ...this.configForm.value };
      if (this.editingId) {
        config.id = this.editingId;
      }
      this.api.saveConfig(config).subscribe({
        next: () => {
          this.saveMessage = this.editingId ? 'Configuration updated!' : 'Configuration created!';
          this.saveError = false;
          this.resetForm();
          this.loadConfigs();
          setTimeout(() => this.saveMessage = '', 3000);
        },
        error: () => {
          this.saveMessage = 'Error saving configuration.';
          this.saveError = true;
          setTimeout(() => this.saveMessage = '', 3000);
        }
      });
    }
  }

  editConfig(config: BotConfig): void {
    this.editingId = config.id ?? null;
    this.configForm.patchValue(config);
  }

  resetForm(): void {
    this.editingId = null;
    this.configForm.reset({
      instrument: 'PF_XBTUSD',
      initialStake: 5,
      maxDoublings: 3,
      takeProfitPct: 1.5,
      stopLossPct: 1.0,
      leverage: 2,
      signalStrategy: 'RSI_EMA',
      active: true,
      demo: false
    });
  }

  deleteConfig(config: BotConfig): void {
    if (config.id && confirm(`Supprimer la config ${config.instrument} ?`)) {
      this.api.deleteConfig(config.id).subscribe({
        next: () => {
          if (this.editingId === config.id) this.resetForm();
          this.loadConfigs();
        },
        error: () => alert('Erreur lors de la suppression')
      });
    }
  }

  clearConfigs(): void {
    if (confirm('Supprimer toutes les configurations ?')) {
      this.api.deleteAllConfigs().subscribe({
        next: () => {
          this.resetForm();
          this.configs = [];
        },
        error: () => alert('Erreur lors de la suppression')
      });
    }
  }
}
