module "lambda_checker" {
  source                  = "./modules/lambda_checker"
  sns_topic_arn           = module.sns.topic_arn
  target_url              = var.target_url
  dynamodb_table_name     = module.dynamodb.table_name
  dynamodb_table_name_arn = module.dynamodb.table_arn

}

module "lambda_fetcher" {
  source = "./modules/lambda_fetcher"

  dynamodb_table_name     = module.dynamodb.table_name
  dynamodb_table_name_arn = module.dynamodb.table_arn

}

module "event_bridge" {
  source                = "./modules/event_bridge"
  checker_function_arn  = module.lambda_checker.checker_function_arn
  checker_function_name = module.lambda_checker.health_check_lambda_name

}

module "s3_fe" {
  source       = "./modules/s3-fe"
  api_endpoint = module.api_gw.api_endpoint

}


module "dynamodb" {
  source = "./modules/dynamodb"

}


module "sns" {
  source         = "./modules/sns"
  email_endpoint = var.email_endpoint
}


module "api_gw" {
  source                = "./modules/api_gw"
  lambda_dashbaord_name = module.lambda_fetcher.dashboard_lambda_name
  lambda_dashboard_arn  = module.lambda_fetcher.dashboard_lambda_arn

}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_checker.health_check_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = module.event_bridge.event_rule
}

