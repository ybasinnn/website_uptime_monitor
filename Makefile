.PHONY: deploy plan destroy

deploy:
	terraform apply --auto-approve

plan:
	terraform plan

destroy:
	terraform destroy --auto-approve
