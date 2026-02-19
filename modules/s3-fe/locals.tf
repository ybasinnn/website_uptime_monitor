locals {
  bucket_name = format("%s-website-health-dashboard", random_pet.bucket_name_prefix.id)
  website_index_path = "website/index.html" 
  api_url = "${var.api_endpoint}/results"
}
