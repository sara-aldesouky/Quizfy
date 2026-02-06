"""
Direct SMTP connection test - bypasses Django to test Gmail auth directly
"""
import smtplib
import os
from django.conf import settings

def test_smtp_connection():
    """Test direct SMTP connection to Gmail"""
    
    print("\n" + "="*60)
    print("DIRECT SMTP CONNECTION TEST")
    print("="*60)
    
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    
    print(f"\nConnecting to: {host}:{port}")
    print(f"User: {user}")
    print(f"Password set: {'YES' if password else 'NO (EMPTY!)'}")
    print(f"TLS enabled: {settings.EMAIL_USE_TLS}")
    
    if not password:
        print("\n❌ ERROR: EMAIL_HOST_PASSWORD is EMPTY!")
        print("   The environment variable is not being read by Django")
        return False
    
    try:
        print("\n[1/3] Creating SMTP connection...")
        server = smtplib.SMTP(host, port, timeout=10)
        print("      ✓ Socket connection successful")
        
        print("\n[2/3] Starting TLS...")
        server.starttls()
        print("      ✓ TLS connection successful")
        
        print("\n[3/3] Authenticating with Gmail...")
        server.login(user, password)
        print("      ✓ Authentication successful!")
        
        server.quit()
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("Gmail SMTP connection is working correctly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION FAILED")
        print(f"   Error: {e}")
        print("\n   Possible causes:")
        print("   1. App password is incorrect")
        print("   2. Password has extra spaces")
        print("   3. Wrong email address")
        print("   4. 2-Step Verification not enabled on Gmail account")
        print("   5. New Gmail account (might need to wait 24 hours)")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP ERROR: {e}")
        print("\n   Possible causes:")
        print("   1. Network connectivity issue")
        print("   2. Gmail is blocking Render's IP")
        print("   3. Port 587 is blocked")
        return False
        
    except TimeoutError:
        print(f"\n❌ CONNECTION TIMEOUT")
        print("   Could not connect to Gmail servers")
        print("   Possible causes:")
        print("   1. Network connectivity issue")
        print("   2. Render's outbound traffic is blocked")
        print("   3. Gmail servers are unreachable")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {e}")
        return False


if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizz_app.settings')
    django.setup()
    test_smtp_connection()
