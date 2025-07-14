import requests
import unittest

API_URL = "http://127.0.0.1:5000"  # Adaptează dacă serverul rulează pe alt port

class TestLicentaAPI(unittest.TestCase):
    results = []

    def test_register(self):
        with open('test_files/login_face.jpg', 'rb') as f:
            files = {'photo': f}
            data = {
                'name': 'testuser',
                'email': 'testuser@example.com',
                'password': 'Test1234!'
            }
            r = requests.post(f"{API_URL}/register", data=data, files=files)
            status = r.status_code in [200, 201]
            self.results.append(('test_register', status, r.status_code, r.json()))
            self.assertIn(r.status_code, [200,201])
            self.assertIn("success", r.json())
            self.assertIn("message", r.json())

    def test_login_with_credentials(self):
        data = {
            'username': 'testuser',
            'password': 'Test1234!'
        }
        r = requests.post(f"{API_URL}/login_with_credentials", data=data)
        status = r.status_code == 200
        self.results.append(('test_login_with_credentials', status, r.status_code, r.json()))
        self.assertEqual(r.status_code, 200)
        self.assertIn("success", r.json())
        self.assertIn("message", r.json())
        # Dacă primești OTP, nu uita să îl trimiți într-un test separat!

    def test_login_face(self):
        with open('test_files/login_face.jpg', 'rb') as f:
            files = {'photo': f}
            r = requests.post(f"{API_URL}/login", files=files)
            status = r.status_code == 200
            self.results.append(('test_login_face', status, r.status_code, r.json()))
            self.assertEqual(r.status_code, 200)
            self.assertIn("success", r.json())
            self.assertIn("message", r.json())

    def test_get_events(self):
        r = requests.get(f"{API_URL}/get_events")
        status = r.status_code == 200
        self.results.append(('test_get_events', status, r.status_code, r.json()))
        self.assertEqual(r.status_code, 200)
        self.assertIn("events", r.json())

    def test_my_events(self):
        params = {'user_name': 'testuser'}
        r = requests.get(f"{API_URL}/my_events", params=params)
        status = r.status_code == 200
        self.results.append(('test_my_events', status, r.status_code, r.json()))
        self.assertEqual(r.status_code, 200)
        self.assertIn("success", r.json())
        self.assertIn("events", r.json())

    def test_verify_access(self):
        with open('test_files/login_face.jpg', 'rb') as f:
            files = {'photo': f}
            data = {'event_name': 'Concert Rock'}
            r = requests.post(f"{API_URL}/verify_access", data=data, files=files)
            status = r.status_code == 200
            self.results.append(('test_verify_access', status, r.status_code, r.json()))
            self.assertEqual(r.status_code, 200)
            self.assertIn("success", r.json())
            self.assertIn("message", r.json())

def save_report(results):
    with open('test_report.txt', 'w', encoding='utf-8') as f:
        all_ok = all(r[1] for r in results)
        f.write("Rezultate testare automata API:\n")
        for name, status, code, resp in results:
            f.write(f"{name}: {'PASSED' if status else 'FAILED'} (status {code})\nRaspuns: {resp}\n\n")
        f.write(f"\n{'TOATE TESTELE AU TRECUT!' if all_ok else 'EXISTA TESTE PICATE!'}\n")

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestLicentaAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    # Salvare raport
    save_report(TestLicentaAPI.results)