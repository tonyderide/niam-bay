import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface User {
  id: number;
  name: string;
  email: string;
}

// Composant avec plusieurs anti-patterns volontaires pour la démo
@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  changeDetection: ChangeDetectionStrategy.Default,  // PERF001: devrait être OnPush
})
export class UserListComponent implements OnInit {
  users: any[] = [];  // TYPE001: any au lieu de User[]
  filteredUsers: any = null;  // TYPE001: any encore
  loading = false;
  errorMessage: any;  // TYPE001: any

  constructor(private http: HttpClient) {}  // ARCH001: HttpClient directement dans le composant

  ngOnInit() {
    this.loading = true;
    console.log('UserListComponent initialized');  // DEBUG001: console.log oublié

    // Mauvaise pratique : pas de gestion du cycle de vie
    this.http.get<User[]>('https://api.example.com/users').subscribe(
      (data) => {
        this.users = data;
        this.filteredUsers = data;
        this.loading = false;
        console.log('Users loaded:', data.length);  // DEBUG001: encore un console.log
      },
      (error) => {
        console.error('Error loading users:', error);
        this.errorMessage = error;
        this.loading = false;
      }
    );

    // Deuxième subscription sans protection — double memory leak
    this.http.get('https://api.example.com/config').subscribe((config) => {
      console.log('Config loaded', config);  // DEBUG001
    });
  }

  filterUsers(query: string): void {
    // Logique de filtre inline au lieu d'être dans un service
    this.filteredUsers = this.users.filter((u: any) =>
      u.name.toLowerCase().includes(query.toLowerCase())
    );
  }

  deleteUser(userId: any): void {  // TYPE001: any
    // ARCH001: appel HTTP direct dans le composant
    this.http.delete(`https://api.example.com/users/${userId}`).subscribe(() => {
      this.users = this.users.filter((u: any) => u.id !== userId);
      console.log('User deleted:', userId);  // DEBUG001
    });
  }
}
