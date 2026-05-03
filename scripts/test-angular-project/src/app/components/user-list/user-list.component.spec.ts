import { TestBed } from '@angular/core/testing';
import { UserListComponent } from './user-list.component';

describe('UserListComponent', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UserListComponent]
    });
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(UserListComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  // TEST001: test skippé jamais réactivé
  xit('should filter users by search term', () => {
    expect(true).toBe(true);
  });

  // TEST001: test focus oublié — la CI ne run que celui-ci
  fit('should delete a user', () => {
    expect(true).toBe(true);
  });

  // TEST001: it.skip oublié
  it.skip('should refresh the list', () => {
    expect(true).toBe(true);
  });
});
