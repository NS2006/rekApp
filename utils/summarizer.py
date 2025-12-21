import torch
from transformers import LEDForConditionalGeneration, LEDTokenizer
import re
import sys

class TextSummarizer:
    def __init__(self, model_path='model'):
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None
        
        # LED model specific constants
        self.MAX_INPUT_LENGTH = 8192
        self.MAX_TARGET_LENGTH = 1024
        
        print(f"Initialized TextSummarizer on {self.device}", file=sys.stderr)

    def _ensure_model_loaded(self):
        """Load model"""
        if self.model is None:
            self.load_model()

    def load_model(self):
        try:
            print(f"Loading model from {self.model_path}...", file=sys.stderr)
            
            self.tokenizer = LEDTokenizer.from_pretrained(self.model_path)
            
            self.model = LEDForConditionalGeneration.from_pretrained(
                self.model_path,
                dtype=torch.float16 if self.device.type == 'cuda' else torch.float32,
                low_cpu_mem_usage=True,
                device_map="auto" if self.device.type == 'cuda' else None
            )
            
            if self.device.type == 'cpu':
                self.model = self.model.to(self.device)
            
            self.model.eval()
            print("Model loaded successfully!", file=sys.stderr)
        except Exception as e:
            print(f"Error loading model: {e}", file=sys.stderr)
            raise

    def summarize(self, text, 
                  num_beams=4, 
                  min_length=40, 
                  length_penalty=1.0, 
                  no_repeat_ngram_size=3, 
                  repetition_penalty=1.5, 
                  encoder_no_repeat_ngram_size=3):
        # Summarizes the full text directly using LED model logic 
        
        self._ensure_model_loaded()

        if not text or len(text.strip()) == 0:
            return "No text provided."

        print(f"📝 Processing full text ({len(text.split())} words) directly...", file=sys.stderr)

        # Pre-processing
        if not re.match(r"^[a-z0-9]+:", text[:10].lower()):
            text = "mtd045pm: " + text

        # Tokenization with Global Attention 
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=self.MAX_INPUT_LENGTH
        ).to(self.device)

        # Set global attention on the first token, because LED need this
        global_attention_mask = torch.zeros_like(inputs["input_ids"])
        global_attention_mask[:, 0] = 1

        # Generate Summary
        try:
            with torch.no_grad():
                summary_ids = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    global_attention_mask=global_attention_mask,
                    num_beams=num_beams,
                    max_length=self.MAX_TARGET_LENGTH,
                    min_length=min_length,
                    length_penalty=length_penalty,
                    no_repeat_ngram_size=no_repeat_ngram_size,
                    repetition_penalty=repetition_penalty,
                    early_stopping=True,
                    encoder_no_repeat_ngram_size=encoder_no_repeat_ngram_size
                )

            # Decoding
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            summary = summary.replace("mtd045pm:", "").strip()
            
            print("Summary generated successfully", file=sys.stderr)
            return summary

        except Exception as e:
            print(f"Summarization error: {e}", file=sys.stderr)
            return f"Error generating summary: {str(e)}"