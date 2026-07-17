import os
import argparse
from pii_detector import PIIDetector
from fake_generator import FakeGenerator
from docx_redactor import DocxRedactor

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="Red Herring Prospectus.docx")
    parser.add_argument("--output", type=str, default="Redacted_Red_Herring_Prospectus.docx")
    args = parser.parse_args()
    
    in_path = os.path.abspath(args.input)
    out_path = os.path.abspath(args.output)
    
    if not os.path.exists(in_path):
        print(f"Error: Input file does not exist at {in_path}")
        return
        
    detector = PIIDetector()
    fake_gen = FakeGenerator()
    redactor = DocxRedactor(detector, fake_gen)
    
    redactor.scan_document(in_path)
    redactor.redact_document(in_path, out_path)
    
    print(f"Redaction complete. Output saved to: {out_path}")

if __name__ == "__main__":
    main()
