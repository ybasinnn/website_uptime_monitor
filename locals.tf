locals {
  bucket_name = format("%s-website-health-dashboard", random_pet.bucket_name_prefix.id)
  website_index_path = "website/index.html" 
  api_url = "${aws_apigatewayv2_api.dashboard_api.api_endpoint}/results"
}
