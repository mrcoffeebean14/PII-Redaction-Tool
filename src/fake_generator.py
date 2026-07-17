import re
import datetime
from faker import Faker

class FakeGenerator:
    def __init__(self):
        # Using Indian and US locales to generate realistic fake names and addresses
        self.fake = Faker(['en_IN', 'en_US'])
        self.mapping = {}
        self.generated_emails = set()
        
    def _preserve_case(self, original, fake_val):
        # Match original string casing (UPPERCASE, lowercase, or Title Case)
        if original.isupper():
            return fake_val.upper()
        if original.islower():
            return fake_val.lower()
        if original.istitle():
            return fake_val.title()
        return fake_val

    def _format_fake_date(self, original_date_str, fake_date):
        # Format fake date to match original date style (slashes, hyphens, or text months)
        try:
            if '/' in original_date_str:
                parts = original_date_str.split('/')
                if len(parts) == 3:
                    if len(parts[0]) == 4:
                        return fake_date.strftime("%Y/%m/%d")
                    else:
                        return fake_date.strftime("%d/%m/%Y")
            elif '-' in original_date_str:
                parts = original_date_str.split('-')
                if len(parts) == 3:
                    if len(parts[0]) == 4:
                        return fake_date.strftime("%Y-%m-%d")
                    else:
                        return fake_date.strftime("%d-%m-%Y")
            
            lower_str = original_date_str.lower()
            months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
            months_short = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            
            has_full = any(m in lower_str for m in months)
            has_short = any(m in lower_str for m in months_short)
            
            if has_full or has_short:
                month_fmt = "%B" if has_full else "%b"
                words = original_date_str.split()
                if len(words) >= 2:
                    if words[0].rstrip(',').isdigit():
                        return fake_date.strftime(f"%d {month_fmt} %Y")
                    else:
                        return fake_date.strftime(f"{month_fmt} %d, %Y")
        except Exception:
            pass
        return fake_date.strftime("%d/%m/%Y")

    def get_fake(self, original_val, entity_type):
        # Ensures same original value gets the exact same replacement throughout the document
        key = original_val.strip()
        if key in self.mapping:
            return self.mapping[key]
            
        fake_val = ""
        
        if entity_type == 'NAME':
            fake_val = self.fake.name()
            parts = key.split()
            if len(parts) >= 3:
                fake_val = f"{self.fake.first_name()} {self.fake.first_name()} {self.fake.last_name()}"
                
        elif entity_type == 'EMAIL':
            prefix = key.split('@')[0]
            clean_prefix = re.sub(r'[^a-zA-Z0-9]', '.', prefix)
            domain = "example.com"
            fake_val = f"{clean_prefix}@{domain}".lower()
            if fake_val in self.generated_emails:
                fake_val = self.fake.email()
            self.generated_emails.add(fake_val)
            
        elif entity_type == 'PHONE':
            if '+91' in key:
                fake_val = f"+91 {self.fake.bothify(text='##########')}"
            else:
                fake_val = self.fake.phone_number()
                
        elif entity_type == 'COMPANY':
            fake_val = self.fake.company()
            lower_orig = key.lower()
            if "private limited" in lower_orig or "pvt ltd" in lower_orig:
                if not fake_val.lower().endswith("private limited") and not fake_val.lower().endswith("pvt. ltd."):
                    fake_val += " Private Limited"
            elif "limited" in lower_orig or "ltd" in lower_orig:
                if not fake_val.lower().endswith("limited") and not fake_val.lower().endswith("ltd"):
                    fake_val += " Limited"
                    
        elif entity_type == 'ADDRESS':
            fake_val = self.fake.address().replace("\n", ", ")
            
        elif entity_type == 'SSN':
            if re.match(r"^\d{4}\s\d{4}\s\d{4}$", key):
                fake_val = self.fake.bothify(text='#### #### ####')
            elif re.match(r"^\d{12}$", key):
                fake_val = self.fake.bothify(text='############')
            elif re.match(r"^[A-Za-z]{5}[0-9]{4}[A-Za-z]$", key):
                fake_val = self.fake.bothify(text='?????####?').upper()
            elif '-' in key:
                fake_val = self.fake.ssn()
            else:
                fake_val = self.fake.bothify(text='?????####?').upper()
                
        elif entity_type == 'CREDIT_CARD':
            fake_val = self.fake.credit_card_number()
            if ' ' in key:
                fake_val = " ".join(fake_val[i:i+4] for i in range(0, len(fake_val), 4))
                
        elif entity_type == 'IP':
            if ':' in key:
                fake_val = self.fake.ipv6()
            else:
                fake_val = self.fake.ipv4()
                
        elif entity_type == 'DOB':
            fake_date = self.fake.date_of_birth(minimum_age=20, maximum_age=60)
            fake_val = self._format_fake_date(key, fake_date)
            
        else:
            fake_val = f"[REDACTED_{entity_type}]"
            
        fake_val = self._preserve_case(original_val, fake_val)
        self.mapping[key] = fake_val
        return fake_val
