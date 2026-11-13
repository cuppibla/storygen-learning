

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
