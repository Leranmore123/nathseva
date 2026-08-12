import json
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from .views import verify_pan


class VerifyPanTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('app.views.requests.post')
    def test_verify_pan_returns_details_from_surepass(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'full_name': 'John Doe',
                'father_name': 'Jane Doe',
                'dob': '1990-01-01',
                'gender': 'Male',
            },
        }
        mock_post.return_value = mock_response

        request = self.factory.post(
            '/api/verify-pan/',
            data=json.dumps({'pan': 'ABCDE1234F'}),
            content_type='application/json',
        )

        response = verify_pan(request)

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body['success'])
        self.assertEqual(body['data']['full_name'], 'John Doe')
        self.assertEqual(body['data']['father_name'], 'Jane Doe')
        self.assertEqual(body['data']['dob'], '1990-01-01')
        self.assertEqual(body['data']['gender'], 'Male')
        mock_post.assert_called_once()
