

# --- 2. Random Name Generator ---
resource "random_pet" "bucket_name_prefix" {
  length    = 2
  separator = "-"
}

# --- 3. S3 Bucket Resource ---
resource "aws_s3_bucket" "dashboard_bucket" {
  bucket = local.bucket_name

  tags = {
    Name = "WebsiteHealthDashboard"
  }
}

# --- 4. Public Access Block (Relaxed for website) ---
resource "aws_s3_bucket_public_access_block" "block_public_access" {
  bucket                  = aws_s3_bucket.dashboard_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# --- 5. Bucket Policy (Allow public s3:GetObject) ---
resource "aws_s3_bucket_policy" "dashboard_bucket_policy" {
  bucket = aws_s3_bucket.dashboard_bucket.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "PublicReadGetObject",
        Effect    = "Allow",
        Principal = "*",
        Action    = "s3:GetObject",
        Resource  = "${aws_s3_bucket.dashboard_bucket.arn}/*",
      },
    ],
  })
}

# --- 6. Website Configuration ---
resource "aws_s3_bucket_website_configuration" "website_config" {
  bucket = aws_s3_bucket.dashboard_bucket.id

  index_document {
    suffix = "index.html"
  }
}

# --- 7. CRITICAL: Upload the index.html template and inject the API URL ---
resource "aws_s3_object" "index_html_upload" {
  bucket       = aws_s3_bucket.dashboard_bucket.id
  key          = "index.html"
  
  # Reads the template file and correctly injects the API URL
  content      = templatefile("${path.module}/website/index.html", { api_endpoint = local.api_url })
  content_type = "text/html"
}