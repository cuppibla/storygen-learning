variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "backend_service_name" {
  description = "Name for the backend Cloud Run service"
  type        = string
  default     = "genai-backend"
}

variable "frontend_service_name" {
  description = "Name for the frontend Cloud Run service"
  type        = string
  default     = "genai-frontend"
}

variable "bucket_name" {
  description = "Name for the Cloud Storage bucket"
  type        = string
}

variable "backend_image" {
  description = "Docker image for backend service"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "frontend_image" {
  description = "Docker image for frontend service"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "secret_name" {
  description = "Name of the secret in Secret Manager"
  type        = string
  default     = "storygen-google-api-key"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 2
}
variable "story_model" {
  description = "Google text model ID"
  type        = string
  default     = "gemini-3.8-flash"
}

variable "image_model" {
  description = "Google Gemini image model ID"
  type        = string
  default     = "gemini-nano-banana-2.1"
}
