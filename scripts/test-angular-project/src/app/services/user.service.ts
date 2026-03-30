import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Ce service est bien fait — pour montrer le contraste avec le composant
@Injectable({ providedIn: 'root' })
export class UserService {
  private apiUrl = 'https://api.example.com';

  constructor(private http: HttpClient) {}

  getUsers(): Observable<any[]> {  // TYPE001: any[] au lieu d'une interface User
    return this.http.get<any[]>(`${this.apiUrl}/users`);
  }

  deleteUser(id: number): Observable<any> {  // TYPE001: any
    return this.http.delete(`${this.apiUrl}/users/${id}`);
  }
}
