# Deploying Nkolo Pass to Render

This guide will help you deploy your Nkolo Pass bus booking application to Render.

## Prerequisites

1. A [Render](https://render.com) account
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. MesomB payment gateway credentials

## Deployment Steps

### 1. Prepare Your Repository

Make sure your code is pushed to a Git repository with all the deployment files:
- `render.yaml` - Render configuration
- `Dockerfile` - Container configuration
- `startup.py` - Database initialization script
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

### 2. Connect to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" and select "Blueprint"
3. Connect your Git repository
4. Render will automatically detect the `render.yaml` file

### 3. Configure Environment Variables

In your Render dashboard, set these environment variables:

#### Required Variables:
```
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
MESOMB_APPLICATION_KEY=your-mesomb-application-key
MESOMB_ACCESS_KEY=your-mesomb-access-key
MESOMB_SECRET_KEY=your-mesomb-secret-key
```

#### Optional Variables (defaults provided):
```
FLASK_ENV=production
MESOMB_BASE_URL=https://mesomb.hachther.com
```

### 4. Deploy

1. Click "Apply" to start the deployment
2. Render will:
   - Create a PostgreSQL database
   - Build your application
   - Set up the web service
   - Initialize the database with default data

### 5. Access Your Application

Once deployed, you can access your application at the provided Render URL.

**Default Admin Credentials:**
- Email: `admin@nkolopass.com`
- Password: `admin123`

**⚠️ Important:** Change the admin password immediately after first login!

## Database

Your application will use:
- **Production:** PostgreSQL database (automatically provisioned by Render)
- **Development:** SQLite database in the `instance/` folder

## File Storage

Static files and uploads are stored on Render's persistent disk. The upload directory is mounted at `/opt/render/project/src/instance`.

## Environment Configuration

The application automatically detects the environment:
- Uses PostgreSQL when `DATABASE_URL` is set (production)
- Falls back to SQLite for local development
- Debug mode is disabled in production (`FLASK_ENV=production`)

## Troubleshooting

### Common Issues:

1. **Build fails with missing dependencies:**
   - Check that all required packages are in `requirements.txt`
   - Ensure Python version compatibility

2. **Database connection errors:**
   - Verify that the PostgreSQL database is properly linked in `render.yaml`
   - Check that `DATABASE_URL` environment variable is set

3. **MesomB payment errors:**
   - Verify all MesomB credentials are correctly set
   - Check that the MesomB API is accessible from your server

4. **Static files not loading:**
   - Ensure the `static/` directory is properly structured
   - Check that upload directories have proper permissions

### Logs

View application logs in the Render dashboard under your service's "Logs" tab.

## Updating Your Application

To update your deployed application:
1. Push changes to your Git repository
2. Render will automatically rebuild and redeploy
3. Database migrations will run during the startup process

## Security Notes

- Change default admin credentials immediately
- Use strong, unique values for `SECRET_KEY`
- Keep MesomB credentials secure and never commit them to your repository
- Regular backup your database data

## Support

For technical issues:
- Check Render's [documentation](https://render.com/docs)
- Review application logs for error details
- Ensure all environment variables are properly configured