// Using localStorage for auth state management
export const authStore = {
  getUser: () => {
    const userData = localStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  },
  
  getToken: () => localStorage.getItem('token'),
  
  login: (user: any, token: string) => {
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('token', token);
  },
  
  logout: () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    window.location.href = '/login';
  },
  
  isAuthenticated: () => !!localStorage.getItem('token')
};