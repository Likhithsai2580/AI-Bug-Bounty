from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import Dataset
import torch

class VulnerabilityDetector:
    def __init__(self, model_name="microsoft/codebert-base"):
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def train(self, train_data, output_dir="./trained_model", num_train_epochs=3):
        train_dataset = Dataset.from_dict({"text": [item["code"] for item in train_data],
                                           "label": [item["is_vulnerable"] for item in train_data]})

        def tokenize_function(examples):
            return self.tokenizer(examples["text"], padding="max_length", truncation=True)

        tokenized_datasets = train_dataset.map(tokenize_function, batched=True)

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir="./logs",
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_datasets,
        )

        trainer.train()
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

    def predict(self, code_snippet):
        inputs = self.tokenizer(code_snippet, return_tensors="pt", padding=True, truncation=True)
        outputs = self.model(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=1)
        return probabilities[0][1].item()  # Probability of being vulnerable

    def fine_tune(self, fine_tuning_data):
        train_dataset = Dataset.from_dict({
            "text": [item["code"] for item in fine_tuning_data],
            "label": [item["is_vulnerable"] for item in fine_tuning_data]
        })

        def tokenize_function(examples):
            return self.tokenizer(examples["text"], padding="max_length", truncation=True)

        tokenized_datasets = train_dataset.map(tokenize_function, batched=True)

        training_args = TrainingArguments(
            output_dir="./fine_tuned_model",
            num_train_epochs=2,
            per_device_train_batch_size=8,
            learning_rate=2e-5,
            weight_decay=0.01,
            logging_dir="./logs",
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_datasets,
        )

        trainer.train()
        self.model.save_pretrained("./fine_tuned_model")
        self.tokenizer.save_pretrained("./fine_tuned_model")

    async def predict_batch(self, code_snippets):
        inputs = self.tokenizer(code_snippets, return_tensors="pt", padding=True, truncation=True)
        outputs = self.model(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=1)
        return probabilities[:, 1].tolist()  # Probabilities of being vulnerable

    def explain_prediction(self, code_snippet):
        from captum.attr import IntegratedGradients
        from captum.attr import visualization as viz

        self.model.eval()
        self.model.zero_grad()

        input_ids = self.tokenizer.encode(code_snippet, return_tensors="pt")
        input_embedding = self.model.get_input_embeddings()(input_ids)

        ig = IntegratedGradients(self.model)
        attributions, delta = ig.attribute(input_embedding, return_convergence_delta=True)

        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        attributions = attributions.sum(dim=-1).squeeze(0)
        attributions = attributions / torch.norm(attributions)
        attributions = attributions.detach().numpy()

        viz.visualize_text(tokens, attributions)