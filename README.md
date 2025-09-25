# Digital Society Management

A complete, robust, sophisticated, and professional Python Flask application for managing housing societies and residential complexes. This system provides comprehensive tools for society administrators to manage members, generate receipts, track finances, and maintain records.

## 🌟 Features

### 🔐 Authentication & Authorization
- **Role-based Access Control**: Super Admin and Society Admin roles
- **Secure Authentication**: Password hashing and session management
- **Registration System**: New society registration with validation
- **Password Recovery**: Email simulation for password reset

### 🏢 Society Management
- **Society Profiles**: Complete society information management
- **Registration Details**: Society name, registration number, year
- **Digital Signatures**: Text or image-based signature support
- **Society Settings**: Address and authority information

### 👥 Member Management
- **Complete Member Profiles**: Name, contact, address information
- **Billing Configuration**: Monthly maintenance, water bills, custom charges
- **Dues Tracking**: Automatic due date calculation and tracking
- **Member Search**: Quick search and filtering capabilities

### 🧾 Receipt Generation
- **Individual Receipts**: Generate receipts for specific members and periods
- **Bulk Generation**: Create multiple receipts simultaneously
- **Automatic Calculations**: Smart calculation of charges based on periods
- **Duplicate Prevention**: Automatic detection of overlapping periods
- **Print-Friendly**: Optimized receipt layouts for printing

### 📊 Dashboard & Analytics
- **Comprehensive Statistics**: Members, receipts, revenue tracking
- **Visual Analytics**: Revenue charts and trends
- **Recent Activity**: Track latest additions and changes
- **Pending Dues Alerts**: Automatic identification of overdue payments

### 💾 Backup & Restore
- **Manual Backups**: Create system backups on demand
- **Automatic Backups**: Scheduled backup system
- **Data Export**: Download backups in JSON format
- **Full Restore**: Complete system restoration from backups

### 🎨 User Interface
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS
- **Dark/Light Theme**: Automatic theme switching with user preference
- **Modern UI Components**: Clean, professional interface design
- **Toast Notifications**: Real-time user feedback system
- **Loading States**: Smooth user experience with loading indicators

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ZakiAli72/Digital-Society-Management.git
   cd Digital-Society-Management
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Login with default Super Admin credentials:
     - **Email**: admin@gmail.com
     - **Password**: password

## 🏗️ Architecture

### Tech Stack
- **Backend**: Python Flask
- **Database**: SQLAlchemy with SQLite (easily configurable for PostgreSQL/MySQL)
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Authentication**: Flask-Login
- **Database Migrations**: Flask-Migrate

### Project Structure
```
Digital-Society-Management/
├── app.py                      # Main application entry point
├── models.py                   # Database models
├── requirements.txt            # Python dependencies
├── routes/                     # Application routes
│   ├── auth.py                # Authentication routes
│   ├── dashboard.py           # Dashboard routes
│   ├── societies.py           # Society management routes
│   ├── members.py             # Member management routes
│   ├── receipts.py            # Receipt generation routes
│   ├── backup.py              # Backup & restore routes
│   └── api.py                 # API endpoints
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── auth/                  # Authentication templates
│   ├── dashboard/             # Dashboard templates
│   └── ...
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   └── img/                   # Images
└── instance/                   # Instance-specific files
    └── digital_society.db     # SQLite database
```

## 📱 Usage

### For Super Administrators
1. **System Overview**: Monitor all societies and their statistics
2. **Society Management**: View and manage all registered societies
3. **Global Analytics**: Access system-wide reports and analytics
4. **Backup Management**: Create and restore system backups
5. **User Management**: Oversee all society administrators

### For Society Administrators
1. **Member Management**: Add, edit, and manage society members
2. **Receipt Generation**: Create individual or bulk receipts
3. **Financial Tracking**: Monitor society finances and dues
4. **Society Profile**: Update society information and settings
5. **Reports**: Generate member and financial reports

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///digital_society.db
# For production, use PostgreSQL:
# DATABASE_URL=postgresql://username:password@host:port/database_name
```

### Database Setup
The application automatically creates the database on first run. For production:
1. Set `DATABASE_URL` to your production database
2. Run database migrations: `flask db upgrade`

## 🚀 Deployment

### Production Deployment
1. **Set production environment variables**
2. **Use a production WSGI server** (e.g., Gunicorn)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
3. **Configure reverse proxy** (Nginx recommended)
4. **Set up SSL certificates** for HTTPS
5. **Configure database backups**

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/ZakiAli72/Digital-Society-Management/issues) page
2. Create a new issue with detailed information
3. Contact the development team

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Email integration for notifications
- [ ] Payment gateway integration
- [ ] Advanced reporting and analytics
- [ ] Multi-language support
- [ ] API documentation with Swagger

---

**Built with ❤️ for housing society management**