build:
	mkdir -p modules/lambda_checker/lambda/build
	pip3 install requests --target modules/lambda_checker/lambda/build/ --upgrade --quiet
	cp modules/lambda_checker/lambda/lambda_function.py modules/lambda_checker/lambda/build/
	cd modules/lambda_checker/lambda/build && zip -r ../website_check.zip .

deploy: build
	terraform apply --auto-approve

plan: build
	terraform plan