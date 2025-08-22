# 🔐 Development Test Accounts

## ✅ **Available Test Accounts**

The following accounts are pre-configured for development testing:

| Email | Password | Role | Description |
|-------|----------|------|-------------|
| `admin@example.com` | `admin` | **Admin** | Full administrative access |
| `researcher@example.com` | `researcher` | User | Basic researcher account |
| `scientist@example.com` | `scientist` | User | Basic scientist account |
| `analyst@example.com` | `analyst` | User | Data analyst account |
| `guest@example.com` | `guest` | User | Guest access account |

## 🚀 **How to Login**

### **Option 1: Direct Login**
1. Go to http://localhost:3000/auth/login
2. Enter any email/password from the table above
3. Click "Login"

### **Option 2: Quick Login (Development Mode)**
- The login page shows a **Development Helper** with quick login buttons
- Click any "Login" button next to a test account
- Automatically logs you in

### **Option 3: Create New Account**
1. Go to http://localhost:3000/auth/signup  
2. Create any email/password you want (will auto-add @example.com if no domain)
3. Account is automatically created in development mode

## 🔧 **Technical Details**

### **Authentication Flow**
- **Development**: Uses in-memory fallback accounts
- **Production**: Would use Active Directory integration
- **Session**: 8-hour cookie-based sessions
- **Security**: Passwords stored in memory (dev only)

### **Account Creation**
```javascript
// Development accounts are created via:
const authService = getAuthService();
await authService.createDevelopmentAccount(username, password, isAdmin);
```

### **API Endpoints**
- `GET /api/auth/session` - Check current session
- `POST /api/auth/login` - Login with credentials  
- `POST /api/auth/signup` - Create new account (dev only)
- `POST /api/auth/logout` - Sign out
- `GET /api/auth/test-accounts` - List available test accounts (dev only)

## 💡 **Development Tips**

### **Quick Access**
```bash
# Access login page
open http://localhost:3000/auth/login

# Access signup page  
open http://localhost:3000/auth/signup

# Test API directly
curl http://localhost:3000/api/auth/test-accounts
```

### **Environment**
- Only works in `NODE_ENV=development`
- Production would require proper AD setup
- All accounts reset when server restarts

## 🔐 **Security Notes**

- **Development only**: These accounts are for testing
- **No persistence**: Accounts reset on server restart  
- **Simple passwords**: Use real passwords in production
- **No encryption**: Dev accounts stored in plain text

## 🎯 **Ready to Use**

The authentication system is fully functional for development:

✅ **Login** - Use any test account above  
✅ **Signup** - Create new accounts in development  
✅ **Sessions** - 8-hour authenticated sessions  
✅ **UI Integration** - Works with Open Canvas interface  
✅ **API Ready** - All endpoints functional  

**Just go to http://localhost:3000/auth/login and use any of the test accounts!** 🎉
