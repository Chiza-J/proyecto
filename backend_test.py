import requests
import sys
import json
import base64
from datetime import datetime
import time

class TechAssistAPITester:
    def __init__(self, base_url="https://techassist-4.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.client_token = None
        self.tech_token = None
        self.client_user = None
        self.tech_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_ticket_id = None
        self.categories = []
        
    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected {expected_status})"
                if response.text:
                    try:
                        error_data = response.json()
                        details += f" - {error_data.get('detail', response.text[:100])}"
                    except:
                        details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration for both client and technician"""
        print("\n🔍 Testing User Registration...")
        
        # Register client
        client_data = {
            "email": f"client_{int(time.time())}@test.com",
            "name": "Test Client",
            "password": "TestPass123!",
            "role": "cliente",
            "phone": "555-1234"
        }
        
        success, response = self.run_test(
            "Register Client",
            "POST",
            "auth/register",
            200,
            data=client_data
        )
        
        if success and 'token' in response:
            self.client_token = response['token']
            self.client_user = response['user']
        
        # Register technician
        tech_data = {
            "email": f"tech_{int(time.time())}@test.com",
            "name": "Test Technician",
            "password": "TestPass123!",
            "role": "tecnico",
            "phone": "555-5678"
        }
        
        success, response = self.run_test(
            "Register Technician",
            "POST",
            "auth/register",
            200,
            data=tech_data
        )
        
        if success and 'token' in response:
            self.tech_token = response['token']
            self.tech_user = response['user']

    def test_user_login(self):
        """Test user login"""
        print("\n🔍 Testing User Login...")
        
        if self.client_user:
            login_data = {
                "email": self.client_user['email'],
                "password": "TestPass123!"
            }
            
            success, response = self.run_test(
                "Client Login",
                "POST",
                "auth/login",
                200,
                data=login_data
            )

    def test_auth_me(self):
        """Test getting current user info"""
        print("\n🔍 Testing Auth Me...")
        
        if self.client_token:
            self.run_test(
                "Get Client Profile",
                "GET",
                "auth/me",
                200,
                token=self.client_token
            )
        
        if self.tech_token:
            self.run_test(
                "Get Technician Profile",
                "GET",
                "auth/me",
                200,
                token=self.tech_token
            )

    def test_categories_and_departments(self):
        """Test getting categories and departments"""
        print("\n🔍 Testing Categories and Departments...")
        
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if success and response:
            self.categories = response
        
        self.run_test(
            "Get Departments",
            "GET",
            "departments",
            200
        )

    def test_ticket_creation(self):
        """Test ticket creation by client"""
        print("\n🔍 Testing Ticket Creation...")
        
        if not self.client_token or not self.categories:
            print("❌ Cannot test ticket creation - missing client token or categories")
            return
        
        # Create a simple base64 image for testing
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        ticket_data = {
            "title": "Test Ticket - Computer Not Working",
            "description": "My computer is not starting up properly. It shows a blue screen error.",
            "category_id": self.categories[0]['id'],
            "attachments": [
                {
                    "filename": "error_screenshot.png",
                    "file_data": test_image
                }
            ]
        }
        
        success, response = self.run_test(
            "Create Ticket with Attachment",
            "POST",
            "tickets",
            200,
            data=ticket_data,
            token=self.client_token
        )
        
        if success and 'id' in response:
            self.created_ticket_id = response['id']

    def test_ticket_retrieval(self):
        """Test ticket retrieval with different user roles"""
        print("\n🔍 Testing Ticket Retrieval...")
        
        # Client should see only their tickets
        if self.client_token:
            self.run_test(
                "Client Get Own Tickets",
                "GET",
                "tickets",
                200,
                token=self.client_token
            )
        
        # Technician should see all tickets
        if self.tech_token:
            self.run_test(
                "Technician Get All Tickets",
                "GET",
                "tickets",
                200,
                token=self.tech_token
            )
            
            self.run_test(
                "Technician Get Assigned Tickets",
                "GET",
                "tickets/my-assigned",
                200,
                token=self.tech_token
            )
            
            self.run_test(
                "Technician Get Resolved Tickets",
                "GET",
                "tickets/my-resolved",
                200,
                token=self.tech_token
            )

    def test_ticket_detail(self):
        """Test getting ticket details"""
        print("\n🔍 Testing Ticket Detail...")
        
        if not self.created_ticket_id:
            print("❌ Cannot test ticket detail - no ticket created")
            return
        
        # Client should be able to see their own ticket
        if self.client_token:
            self.run_test(
                "Client Get Own Ticket Detail",
                "GET",
                f"tickets/{self.created_ticket_id}",
                200,
                token=self.client_token
            )
        
        # Technician should be able to see any ticket
        if self.tech_token:
            self.run_test(
                "Technician Get Ticket Detail",
                "GET",
                f"tickets/{self.created_ticket_id}",
                200,
                token=self.tech_token
            )

    def test_ticket_updates(self):
        """Test ticket updates by technician"""
        print("\n🔍 Testing Ticket Updates...")
        
        if not self.created_ticket_id or not self.tech_token:
            print("❌ Cannot test ticket updates - missing ticket or tech token")
            return
        
        # Test status update
        self.run_test(
            "Update Ticket Status",
            "PUT",
            f"tickets/{self.created_ticket_id}",
            200,
            data={"status": "en_proceso"},
            token=self.tech_token
        )
        
        # Test priority update
        self.run_test(
            "Update Ticket Priority",
            "PUT",
            f"tickets/{self.created_ticket_id}",
            200,
            data={"priority": "media"},
            token=self.tech_token
        )
        
        # Test technician assignment
        if self.tech_user:
            self.run_test(
                "Assign Technician to Ticket",
                "PUT",
                f"tickets/{self.created_ticket_id}",
                200,
                data={"technician_id": self.tech_user['id']},
                token=self.tech_token
            )

    def test_comments(self):
        """Test adding comments to tickets"""
        print("\n🔍 Testing Comments...")
        
        if not self.created_ticket_id:
            print("❌ Cannot test comments - no ticket created")
            return
        
        # Client adds comment
        if self.client_token:
            self.run_test(
                "Client Add Comment",
                "POST",
                f"tickets/{self.created_ticket_id}/comments",
                200,
                data={"comment": "I tried restarting but the problem persists."},
                token=self.client_token
            )
        
        # Technician adds comment
        if self.tech_token:
            self.run_test(
                "Technician Add Comment",
                "POST",
                f"tickets/{self.created_ticket_id}/comments",
                200,
                data={"comment": "I will check the hardware components."},
                token=self.tech_token
            )

    def test_users_endpoints(self):
        """Test user-related endpoints"""
        print("\n🔍 Testing User Endpoints...")
        
        if self.tech_token:
            self.run_test(
                "Get All Users (Technician)",
                "GET",
                "users",
                200,
                token=self.tech_token
            )
            
            self.run_test(
                "Get Technicians List",
                "GET",
                "users/technicians",
                200,
                token=self.tech_token
            )
        
        # Client should not be able to access user lists
        if self.client_token:
            self.run_test(
                "Client Access Users (Should Fail)",
                "GET",
                "users",
                403,
                token=self.client_token
            )

    def test_equipments(self):
        """Test equipment endpoints"""
        print("\n🔍 Testing Equipment Endpoints...")
        
        if self.client_token:
            self.run_test(
                "Get Equipments",
                "GET",
                "equipments",
                200,
                token=self.client_token
            )

    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        print("\n🔍 Testing Unauthorized Access...")
        
        # Test accessing protected endpoints without token
        self.run_test(
            "Access Tickets Without Token",
            "GET",
            "tickets",
            401
        )
        
        self.run_test(
            "Access Profile Without Token",
            "GET",
            "auth/me",
            401
        )

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting TechAssist API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Test sequence
        self.test_user_registration()
        self.test_user_login()
        self.test_auth_me()
        self.test_categories_and_departments()
        self.test_ticket_creation()
        self.test_ticket_retrieval()
        self.test_ticket_detail()
        self.test_ticket_updates()
        self.test_comments()
        self.test_users_endpoints()
        self.test_equipments()
        self.test_unauthorized_access()
        
        # Print summary
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TechAssistAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())