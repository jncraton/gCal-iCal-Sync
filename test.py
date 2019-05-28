import unittest
import main
import mock

class TestMain(unittest.TestCase):
  def test_upper(self):
    service = mock.MagicMock()
    new_events = {}

    events = main.handle_existing_events(service,new_events)
    self.assertEqual(len(new_events), 0)

if __name__ == '__main__':
  unittest.main()