import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from datetime import datetime, timedelta
from plyer import notification
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.togglebutton import ToggleButton

scheduler = BackgroundScheduler()
scheduler.start()

DATA_FILE = 'secure_data.json'


class URLRow(BoxLayout):
    daily_gain = NumericProperty(0)
    date = StringProperty('')
    notification_enabled = BooleanProperty(False)
    done = BooleanProperty(False)  # Initialize the done property

    def __init__(self, url='', email='', password='', invested='', gain='', date='', notification_enabled=False, done=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40

        # Unique identifier for the notification job
        self.notification_job_id = f"notification_{id(self)}"

        # Adding input fields
        self.url_input = TextInput(hint_text='URL', size_hint_x=2, text=url, multiline=False)
        self.email_input = TextInput(hint_text='Email', text=email, multiline=False)
        self.password_input = TextInput(hint_text='Password', text=password, multiline=False, password=True)
        self.toggle_password_btn = Button(text='Show', size_hint_x=None, width=70)
        self.invested_input = TextInput(hint_text='Investment', text=invested, multiline=False)
        self.gain_input = TextInput(hint_text='Daily Gain', text=gain, multiline=False)
        self.date_input = TextInput(hint_text='Date', text=date, multiline=False)

        # Toggle button for task completion
        self.done = done
        self.done_btn = Button(text='Done' if self.done else 'Not Done', size_hint_x=None, width=80,
                               background_color=(0, 1, 0, 1) if self.done else (1, 0, 0, 1))
        self.done_btn.bind(on_press=self.toggle_done)

        # Delete button
        self.delete_btn = Button(text='Delete', size_hint_x=None, width=80)
        self.delete_btn.bind(on_press=self.delete_row)

        # Notification toggle
        self.notification_btn = ToggleButton(text='Notify On' if notification_enabled else 'Notify Off',
                                             state='down' if notification_enabled else 'normal',
                                             size_hint_x=None, width=100)
        self.notification_btn.bind(on_press=self.toggle_notification)

        # Add widgets to layout
        self.add_widget(self.url_input)
        self.add_widget(self.email_input)
        self.add_widget(self.password_input)
        self.add_widget(self.toggle_password_btn)
        self.add_widget(self.invested_input)
        self.add_widget(self.gain_input)
        self.add_widget(self.date_input)
        self.add_widget(self.done_btn)
        self.add_widget(self.notification_btn)
        self.add_widget(self.delete_btn)

        self.toggle_password_btn.bind(on_press=self.prompt_pin)
        self.update_background()

    def toggle_notification(self, instance):
        self.notification_enabled = not self.notification_enabled
        instance.text = 'Notify On' if self.notification_enabled else 'Notify Off'
        self.update_background()
        if self.notification_enabled:
            self.schedule_notification()
        else:
            self.cancel_notification()

    def schedule_notification(self):
        # Example logic: Schedule a notification 24 hours later for this URL
        notification_time = datetime.now() + timedelta(hours=24)
        scheduler.add_job(self.send_notification, 'date', run_date=notification_time, id=self.notification_job_id)

    def cancel_notification(self):
        try:
            scheduler.remove_job(self.notification_job_id)
        except Exception as e:
            print(f"Error canceling notification: {e}")

    def update_background(self):
        self.background_color = [0, 0.5, 0.5, 1] if self.notification_enabled else [1, 1, 1, 1]

    def prompt_pin(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=5)
        pin_input = TextInput(hint_text='Enter PIN', password=True, multiline=False)
        confirm_button = Button(text='Confirm', size_hint_y=None, height=30)

        layout.add_widget(pin_input)
        layout.add_widget(confirm_button)

        popup = Popup(title='Enter PIN to Show Password', content=layout, size_hint=(0.7, 0.3))
        confirm_button.bind(on_press=lambda x: self.verify_pin(popup, pin_input.text))
        popup.open()

    def verify_pin(self, popup, entered_pin):
        app_data = SecureApp.get_data()
        if app_data.get('pin') == entered_pin:
            popup.dismiss()
            if self.password_input.password:
                self.password_input.password = False
                self.toggle_password_btn.text = 'Hide'
            else:
                self.password_input.password = True
                self.toggle_password_btn.text = 'Show'
        else:
            error_popup = Popup(title='Error', content=Label(text='Invalid PIN'), size_hint=(0.5, 0.2))
            error_popup.open()

    def toggle_done(self, instance):
        self.done = not self.done
        self.done_btn.text = 'Done' if self.done else 'Not Done'
        self.done_btn.background_color = (0, 1, 0, 1) if self.done else (1, 0, 0, 1)

    def delete_row(self, instance):
        self.cancel_notification()  # Ensure the notification is canceled if the row is deleted
        self.parent.remove_widget(self)

    def get_data(self):
        return {
            'url': self.url_input.text,
            'email': self.email_input.text,
            'password': self.password_input.text,
            'invested': self.invested_input.text,
            'gain': self.gain_input.text,
            'date': self.date_input.text,
            'notification_enabled': self.notification_enabled,
            'done': self.done
        }

    def send_notification(self):
        notification.notify(title='URL Notification', message=f'Reminder: Check URL {self.url_input.text}')


class SecureApp(App):
    def build(self):
        self.logged_in = False
        self.root = BoxLayout(orientation='vertical', spacing=20, padding=20)
        self.main_screen = BoxLayout(orientation='vertical', spacing=10)
        
        center_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        login_button = Button(text='Login', size_hint=(None, None), size=(100, 50))
        register_button = Button(text='Register', size_hint=(None, None), size=(100, 50))
        
        center_box.add_widget(login_button)
        center_box.add_widget(register_button)

        login_button.bind(on_press=self.show_login_popup)
        register_button.bind(on_press=self.show_register_popup)

        self.main_screen.add_widget(center_box)
        self.root.add_widget(self.main_screen)
        
        return self.root

    def show_login_popup(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=5)
        username_input = TextInput(hint_text='Username', multiline=False)
        password_input = TextInput(hint_text='Password', password=True, multiline=False)
        pin_input = TextInput(hint_text='PIN', password=True, multiline=False)

        login_button = Button(text='Login', size_hint_y=None, height=30)
        layout.add_widget(username_input)
        layout.add_widget(password_input)
        layout.add_widget(pin_input)
        layout.add_widget(login_button)

        popup = Popup(title='Login', content=layout, size_hint=(0.8, 0.5))
        login_button.bind(on_press=lambda x: self.verify_login(popup, username_input.text, password_input.text, pin_input.text))

        popup.open()

    def verify_login(self, popup, username, password, pin):
        data = self.load_data()

        if data.get('username') == username and data.get('password') == password and data.get('pin') == pin:
            self.logged_in = True
            popup.dismiss()
            self.show_secure_area()
        else:
            error_popup = Popup(title='Login Error', content=Label(text='Invalid credentials'), size_hint=(0.6, 0.4))
            error_popup.open()

    def show_register_popup(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=5)

        username_input = TextInput(hint_text='New Username', multiline=False)
        password_input = TextInput(hint_text='New Password', password=True, multiline=False)
        pin_input = TextInput(hint_text='New PIN', password=True, multiline=False)

        register_button = Button(text='Register', size_hint_y=None, height=30)
        layout.add_widget(username_input)
        layout.add_widget(password_input)
        layout.add_widget(pin_input)
        layout.add_widget(register_button)

        popup = Popup(title='Register', content=layout, size_hint=(0.8, 0.5))
        register_button.bind(on_press=lambda x: self.register_user(popup, username_input.text, password_input.text, pin_input.text))

        popup.open()

    def register_user(self, popup, username, password, pin):
        if not username or not password or not pin:
            error_popup = Popup(title='Error', content=Label(text='All fields are required'), size_hint=(0.6, 0.4))
            error_popup.open()
            return

        data = {
            'username': username,
            'password': password,
            'pin': pin,
            'urls': []
        }
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, indent=4)

        popup.dismiss()

    def show_secure_area(self):
        self.main_screen.clear_widgets()

        notification_button = Button(text='Set Notification', size_hint_y=None, height=50)
        notification_button.bind(on_press=self.show_notification_popup)

        # Use a GridLayout within the ScrollView for better organization and flexibility
        self.url_rows_layout = GridLayout(cols=1, size_hint_y=None)
        self.url_rows_layout.bind(minimum_height=self.url_rows_layout.setter('height'))

        scroll_view = ScrollView(size_hint=(1, None), size=(500, 300))  # Set width and height as needed
        scroll_view.add_widget(self.url_rows_layout)
        
        add_button = Button(text='Add URL Row', size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_url_row)

        save_button = Button(text='Save Data', size_hint_y=None, height=50)
        save_button.bind(on_press=self.save_data)

        self.main_screen.add_widget(notification_button)
        self.main_screen.add_widget(scroll_view)
        self.main_screen.add_widget(add_button)
        self.main_screen.add_widget(save_button)
        
        self.load_and_display_rows()

    def load_and_display_rows(self):
        self.url_rows_layout.clear_widgets()
        url_rows_data = self.load_data().get('urls', [])
        for url_row_data in url_rows_data:
            url_row = URLRow(**url_row_data)
            self.url_rows_layout.add_widget(url_row)

    def add_url_row(self, instance):
        new_row = URLRow()
        self.url_rows_layout.add_widget(new_row)
        # Scroll to the bottom of the scroll view to view the new row
        self.url_rows_layout.parent.scroll_y = 0

    def load_data(self):
        try:
            with open(DATA_FILE, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_data(self, instance=None):
        urls = [url_row.get_data() for url_row in self.url_rows_layout.children]
        data = self.load_data()
        data['urls'] = urls
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, indent=4)

    def show_notification_popup(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(None, None), width=400, height=400)
        date_input = TextInput(hint_text='Enter date (YYYY-MM-DD)', size_hint_y=None, height=40)
        time_input = TextInput(hint_text='Enter time (HH:MM)', size_hint_y=None, height=40)
        message_input = TextInput(hint_text='Message (URL)', size_hint_y=None, height=40)
        set_button = Button(text='Schedule Notification', size_hint_y=None, height=40)
        layout.add_widget(date_input)
        layout.add_widget(time_input)
        layout.add_widget(message_input)
        layout.add_widget(set_button)

        popup = Popup(title='Set Notification', content=layout, size_hint=(0.8, 0.5), auto_dismiss=True)
        set_button.bind(on_press=lambda x: self.schedule_notification(date_input.text, time_input.text, message_input.text, popup))
        popup.open()

    def schedule_notification(self, date_str, time_str, message, popup):
        try:
            notification_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            local_tz = pytz.timezone('Europe/Lisbon')
            notification_time = local_tz.localize(notification_time)
        except ValueError:
            error_popup = Popup(title='Error', content=Label(text='Invalid date/time format.'), size_hint=(0.6, 0.3))
            error_popup.open()
            return

        scheduler.add_job(lambda: self.send_notification(message), 'date', run_date=notification_time)
        popup.dismiss()

    def send_notification(self, message):
        notification.notify(title='Scheduled Notification', message=message)

    def load_and_display_rows(self):
        self.url_rows_layout.clear_widgets()
        url_rows_data = self.load_data().get('urls', [])
        for url_row_data in url_rows_data:
            url_row = URLRow(**url_row_data)
            self.url_rows_layout.add_widget(url_row)
    
    
    @staticmethod
    def get_data():
        try:
            with open(DATA_FILE, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}


if __name__ == '__main__':
    SecureApp().run()
