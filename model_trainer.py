import logging
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import Dataset
import torch

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, model_name="microsoft/codebert-base"):
        logger.debug(f"Initializing ModelTrainer with model_name: {model_name}")
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.debug("ModelTrainer initialized")

    def train(self, train_data, output_dir="./trained_model", num_train_epochs=3):
        logger.debug(f"Starting training with {len(train_data)} samples, output_dir: {output_dir}, num_train_epochs: {num_train_epochs}")
        train_dataset = Dataset.from_dict({"text": [item["code"] for item in train_data],
                                           "label": [item["is_vulnerable"] for item in train_data]})
        logger.debug(f"Train dataset created with {len(train_dataset)} samples")

        def tokenize_function(examples):
            logger.debug(f"Tokenizing {len(examples['text'])} examples")
            return self.tokenizer(examples["text"], padding="max_length", truncation=True)

        tokenized_datasets = train_dataset.map(tokenize_function, batched=True)
        logger.debug("Dataset tokenized")

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir="./logs",
        )
        logger.debug(f"Training arguments set: {training_args}")

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_datasets,
        )
        logger.debug("Trainer initialized")

        logger.debug("Starting training")
        trainer.train()
        logger.debug("Training completed")

        logger.debug(f"Saving model to {output_dir}")
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        logger.debug("Model and tokenizer saved")

    def predict(self, code_snippet):
        logger.debug(f"Predicting vulnerability for code snippet: {code_snippet[:50]}...")
        inputs = self.tokenizer(code_snippet, return_tensors="pt", padding=True, truncation=True)
        logger.debug(f"Inputs tokenized: {inputs}")
        outputs = self.model(**inputs)
        logger.debug(f"Model outputs: {outputs}")
        probabilities = torch.softmax(outputs.logits, dim=1)
        logger.debug(f"Probabilities: {probabilities}")
        vulnerability_prob = probabilities[0][1].item()
        logger.debug(f"Vulnerability probability: {vulnerability_prob}")
        return vulnerability_prob

    def fine_tune(self, fine_tuning_data):
        logger.debug(f"Starting fine-tuning with {len(fine_tuning_data)} samples")
        train_dataset = Dataset.from_dict({
            "text": [item["code"] for item in fine_tuning_data],
            "label": [item["is_vulnerable"] for item in fine_tuning_data]
        })
        logger.debug(f"Fine-tuning dataset created with {len(train_dataset)} samples")

        def tokenize_function(examples):
            logger.debug(f"Tokenizing {len(examples['text'])} examples for fine-tuning")
            return self.tokenizer(examples["text"], padding="max_length", truncation=True)

        tokenized_datasets = train_dataset.map(tokenize_function, batched=True)
        logger.debug("Fine-tuning dataset tokenized")

        training_args = TrainingArguments(
            output_dir="./fine_tuned_model",
            num_train_epochs=2,
            per_device_train_batch_size=8,
            learning_rate=2e-5,
            weight_decay=0.01,
            logging_dir="./logs",
        )
        logger.debug(f"Fine-tuning arguments set: {training_args}")

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_datasets,
        )
        logger.debug("Fine-tuning trainer initialized")

        logger.debug("Starting fine-tuning")
        trainer.train()
        logger.debug("Fine-tuning completed")

        logger.debug("Saving fine-tuned model")
        self.model.save_pretrained("./fine_tuned_model")
        self.tokenizer.save_pretrained("./fine_tuned_model")
        logger.debug("Fine-tuned model and tokenizer saved")

    async def predict_batch(self, code_snippets):
        logger.debug(f"Predicting vulnerabilities for {len(code_snippets)} code snippets")
        inputs = self.tokenizer(code_snippets, return_tensors="pt", padding=True, truncation=True)
        logger.debug(f"Batch inputs tokenized: {inputs}")
        outputs = self.model(**inputs)
        logger.debug(f"Batch model outputs: {outputs}")
        probabilities = torch.softmax(outputs.logits, dim=1)
        logger.debug(f"Batch probabilities: {probabilities}")
        vulnerability_probs = probabilities[:, 1].tolist()
        logger.debug(f"Batch vulnerability probabilities: {vulnerability_probs}")
        return vulnerability_probs

    def explain_prediction(self, code_snippet):
        logger.debug(f"Explaining prediction for code snippet: {code_snippet[:50]}...")
        from captum.attr import IntegratedGradients
        from captum.attr import visualization as viz

        self.model.eval()
        self.model.zero_grad()
        logger.debug("Model set to evaluation mode and gradients zeroed")

        input_ids = self.tokenizer.encode(code_snippet, return_tensors="pt")
        logger.debug(f"Input IDs: {input_ids}")
        input_embedding = self.model.get_input_embeddings()(input_ids)
        logger.debug(f"Input embedding shape: {input_embedding.shape}")

        ig = IntegratedGradients(self.model)
        logger.debug("IntegratedGradients initialized")
        attributions, delta = ig.attribute(input_embedding, return_convergence_delta=True)
        logger.debug(f"Attributions shape: {attributions.shape}, Convergence delta: {delta}")

        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        logger.debug(f"Tokens: {tokens}")
        attributions = attributions.sum(dim=-1).squeeze(0)
        attributions = attributions / torch.norm(attributions)
        attributions = attributions.detach().numpy()
        logger.debug(f"Normalized attributions shape: {attributions.shape}")

        logger.debug("Visualizing text attributions")
        viz.visualize_text(tokens, attributions)
        logger.debug("Visualization complete")