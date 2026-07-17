import sys
from pii_detector import PIIDetector

EVAL_DATA = [
    {
        "text": "Registered Office: 11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India;",
        "pii": [
            {"text": "11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India", "type": "ADDRESS"}
        ]
    },
    {
        "text": "Corporate Office: 201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411 045, Maharashtra, India;",
        "pii": [
            {"text": "201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411 045, Maharashtra, India", "type": "ADDRESS"}
        ]
    },
    {
        "text": "Contact Person: Sarthak Malvadkar, Company Secretary and Compliance Officer;",
        "pii": [
            {"text": "Sarthak Malvadkar", "type": "NAME"}
        ]
    },
    {
        "text": "Telephone: + 91 20 4505 3237; E-mail: cs.connect@kshinternational.com; Website: www.kshinternational.com",
        "pii": [
            {"text": "+ 91 20 4505 3237", "type": "PHONE"},
            {"text": "cs.connect@kshinternational.com", "type": "EMAIL"}
        ]
    },
    {
        "text": "KSH INTERNATIONAL LIMITED was originally incorporated as Bhandary Metal Extrusion Private Limited under the provisions of the Companies Act, 1956.",
        "pii": [
            {"text": "KSH INTERNATIONAL LIMITED", "type": "COMPANY"},
            {"text": "Bhandary Metal Extrusion Private Limited", "type": "COMPANY"}
        ]
    },
    {
        "text": "OUR PROMOTERS: KUSHAL SUBBAYYA HEGDE, PUSHPA KUSHAL HEGDE, RAJESH KUSHAL HEGDE, ROHIT KUSHAL HEGDE, RAKHI GIRIJA SHETTY",
        "pii": [
            {"text": "KUSHAL SUBBAYYA HEGDE", "type": "NAME"},
            {"text": "PUSHPA KUSHAL HEGDE", "type": "NAME"},
            {"text": "RAJESH KUSHAL HEGDE", "type": "NAME"},
            {"text": "ROHIT KUSHAL HEGDE", "type": "NAME"},
            {"text": "RAKHI GIRIJA SHETTY", "type": "NAME"}
        ]
    },
    {
        "text": "The Designated RTA Locations or the Escrow Collection Bank shall be notified of the Cap Price.",
        "pii": []
    },
    {
        "text": "The document is dated December 10, 2025. Today is June 15, 2026.",
        "pii": []
    },
    {
        "text": "He was born on July 30, 1979. His Date of Birth is July 30, 1979.",
        "pii": [
            {"text": "July 30, 1979", "type": "DOB"},
            {"text": "July 30, 1979", "type": "DOB"}
        ]
    },
    {
        "text": "Please read section 32 of the Companies Act, 2013 and SEBI ICDR Regulations.",
        "pii": []
    },
    {
        "text": "The server IP address is 192.168.1.1 and the backup is 2001:0db8:85a3:0000:0000:8a2e:0370:7334.",
        "pii": [
            {"text": "192.168.1.1", "type": "IP"},
            {"text": "2001:0db8:85a3:0000:0000:8a2e:0370:7334", "type": "IP"}
        ]
    },
    {
        "text": "For any queries, contact our Book Running Lead Managers or the Registrar of Companies, Maharashtra, Pune.",
        "pii": []
    },
    {
        "text": "Mr. Thomas Daniel Merritt has SSN 123-45-6789.",
        "pii": [
            {"text": "Thomas Daniel Merritt", "type": "NAME"},
            {"text": "123-45-6789", "type": "SSN"}
        ]
    },
    {
        "text": "His Indian PAN is ABCDE1234F and Aadhaar is 1234 5678 9012.",
        "pii": [
            {"text": "ABCDE1234F", "type": "SSN"},
            {"text": "1234 5678 9012", "type": "SSN"}
        ]
    },
    {
        "text": "Please credit my card 4111-1111-1111-1111 for the payment.",
        "pii": [
            {"text": "4111-1111-1111-1111", "type": "CREDIT_CARD"}
        ]
    },
    {
        "text": "Our company works with Nuvama Wealth Management Limited and ICICI Securities Limited.",
        "pii": [
            {"text": "Nuvama Wealth Management Limited", "type": "COMPANY"},
            {"text": "ICICI Securities Limited", "type": "COMPANY"}
        ]
    },
    {
        "text": "The UPI mandate end time and date shall be at 5:00 p.m. on Bid/Offer Closing Day.",
        "pii": []
    },
    {
        "text": "Kushal Kushal Hegde and Rohit Kushal Hegde are directors.",
        "pii": [
            {"text": "Kushal Kushal Hegde", "type": "NAME"},
            {"text": "Rohit Kushal Hegde", "type": "NAME"}
        ]
    },
    {
        "text": "She was born on 15-08-1988.",
        "pii": [
            {"text": "15-08-1988", "type": "DOB"}
        ]
    },
    {
        "text": "Visit our website at www.kshinternational.com for more info.",
        "pii": []
    }
]

def run_evaluation():
    detector = PIIDetector()
    pii_types = ["NAME", "EMAIL", "PHONE", "COMPANY", "ADDRESS", "SSN", "CREDIT_CARD", "DOB", "IP"]
    metrics = {t: {"TP": 0, "FP": 0, "FN": 0} for t in pii_types}
    
    for i, item in enumerate(EVAL_DATA):
        text = item["text"]
        ground_truth = item["pii"]
        
        detections = detector.detect(text)
        gt_matched = [False] * len(ground_truth)
        det_matched = [False] * len(detections)
        
        for gt_idx, gt in enumerate(ground_truth):
            gt_text = gt["text"].strip().lower()
            gt_type = gt["type"]
            
            for det_idx, det in enumerate(detections):
                det_text = det["text"].strip().lower()
                det_type = det["type"]
                
                if not det_matched[det_idx] and gt_type == det_type and (gt_text in det_text or det_text in gt_text):
                    gt_matched[gt_idx] = True
                    det_matched[det_idx] = True
                    metrics[gt_type]["TP"] += 1
                    break
            
            if not gt_matched[gt_idx]:
                metrics[gt_type]["FN"] += 1
                
        for det_idx, det in enumerate(detections):
            if not det_matched[det_idx]:
                det_type = det["type"]
                metrics[det_type]["FP"] += 1

    print("\n" + "="*50)
    print("PII REDACTION TOOL EVALUATION REPORT")
    print("="*50)
    print(f"{'PII Type':<15} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-"*75)
    
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for t in pii_types:
        tp = metrics[t]["TP"]
        fp = metrics[t]["FP"]
        fn = metrics[t]["FN"]
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0
        
        print(f"{t:<15} | {tp:<4} | {fp:<4} | {fn:<4} | {precision:.4f}    | {recall:.4f} | {f1:.4f}")
        
    print("-"*75)
    
    g_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    g_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    g_f1 = 2 * (g_precision * g_recall) / (g_precision + g_recall) if (g_precision + g_recall) > 0 else 1.0
    
    print(f"{'OVERALL':<15} | {total_tp:<4} | {total_fp:<4} | {total_fn:<4} | {g_precision:.4f}    | {g_recall:.4f} | {g_f1:.4f}")
    print("="*50)

if __name__ == "__main__":
    run_evaluation()
