import os
import socket
import time
from dotenv import load_dotenv
import psycopg2
import sys
import subprocess

load_dotenv()

postgres_url = os.getenv("POSTGRES_URL")
print(f"Connection string: {postgres_url}")

# Get system information
print("\nSystem Information:")
print(f"  Python version: {sys.version}")
print(f"  Current directory: {os.getcwd()}")
print(f"  Environment variables:")
for key in ["POSTGRES_URL", "PORT", "AWS_REGION", "AWS_EB_REGION"]:
    print(f"    {key}: {os.getenv(key, 'Not set')}")

try:
    # Parse the connection string
    # Format: postgresql://username:password@host:port/dbname
    # or postgresql+psycopg2://username:password@host:port/dbname
    if postgres_url.startswith("postgresql://") or postgres_url.startswith("postgresql+psycopg2://"):
        # Remove the protocol part
        conn_str = postgres_url.replace("postgresql://", "").replace("postgresql+psycopg2://", "")
        
        # Split into credentials and host parts
        creds, host_part = conn_str.split("@", 1)
        
        # Extract username and password
        username, password = creds.split(":", 1)
        
        # Extract host, port, and database
        host_port, database = host_part.rsplit("/", 1)
        
        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host = host_port
            port = "5432"  # Default PostgreSQL port
        
        print(f"\nParsed connection parameters:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password)}")
        
        # Test network connectivity to the host
        print(f"\nTesting network connectivity to {host}:{port}...")
        try:
            # Try to resolve the hostname
            print(f"Resolving hostname {host}...")
            ip_address = socket.gethostbyname(host)
            print(f"Resolved to IP address: {ip_address}")
            
            # Try to establish a TCP connection
            print(f"Attempting to establish TCP connection to {host}:{port}...")
            start_time = time.time()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)  # 10 second timeout
            result = s.connect_ex((host, int(port)))
            end_time = time.time()
            
            if result == 0:
                print(f"TCP connection successful! Time taken: {end_time - start_time:.2f} seconds")
            else:
                print(f"TCP connection failed with error code: {result}")
                print(f"This might indicate network connectivity issues or firewall restrictions.")
            s.close()
        except socket.gaierror:
            print(f"Hostname resolution failed for {host}")
        except socket.timeout:
            print(f"Connection attempt timed out after 10 seconds")
        except Exception as e:
            print(f"Network test error: {e}")
        
        # Try to connect using psycopg2
        print("\nAttempting connection with psycopg2...")
        print("Setting connection timeout to 30 seconds...")
        
        start_time = time.time()
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=database,
                user=username,
                password=password,
                connect_timeout=30  # 30 second timeout
            )
            end_time = time.time()
            print(f"Connection successful! Time taken: {end_time - start_time:.2f} seconds")
            
            # Test creating a table
            print("\nTesting database operations...")
            cursor = conn.cursor()
            
            # Create a test table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_name VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Insert a test record
            cursor.execute("""
            INSERT INTO connection_test (test_name) VALUES (%s)
            """, ("eb_deployment_test",))
            
            # Commit the transaction
            conn.commit()
            
            # Query the test record
            cursor.execute("SELECT * FROM connection_test ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            print(f"Test record created: {result}")
            
            # Close the cursor and connection
            cursor.close()
            conn.close()
            print("Database operations completed successfully!")
        except psycopg2.OperationalError as e:
            end_time = time.time()
            print(f"Connection failed after {end_time - start_time:.2f} seconds")
            print(f"Error: {e}")
            
            # Provide more detailed diagnostics
            if "timeout" in str(e).lower():
                print("\nTimeout Error Analysis:")
                print("1. The database server might be unreachable due to network issues")
                print("2. Security groups or firewall rules might be blocking the connection")
                print("3. The database instance might be in a different region or VPC")
                print("4. The database instance might be stopped or terminated")
                
                # Suggest solutions
                print("\nPossible Solutions:")
                print("1. Check if the database is in the same region as the application")
                print("2. Verify security group rules allow connections from the application")
                print("3. Check if the database instance is running")
                print("4. Consider using an RDS proxy or VPC peering for cross-region connections")
            elif "password" in str(e).lower():
                print("\nAuthentication Error Analysis:")
                print("The username or password in the connection string might be incorrect")
            
            sys.exit(1)
        
    else:
        print(f"Connection string doesn't start with 'postgresql://' or 'postgresql+psycopg2://'")
        print(f"Current format: {postgres_url.split('://')[0] if '://' in postgres_url else 'unknown'}")
        
        # Try modifying the connection string
        if postgres_url.startswith("postgresql+psycopg2://"):
            modified_url = postgres_url.replace("postgresql+psycopg2://", "postgresql://")
            print(f"\nTrying with modified connection string (postgresql:// instead of postgresql+psycopg2://)...")
            os.environ["POSTGRES_URL"] = modified_url
            print(f"Modified connection string: {modified_url}")
            # Recursive call with modified URL
            import test_eb_db_connection
            sys.exit(0)
        
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
    sys.exit(1)

print("\nAll tests passed successfully!")
sys.exit(0)
