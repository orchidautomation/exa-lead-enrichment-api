import os
import sys
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.exa import ExaTools
from pydantic import BaseModel, Field
from typing import List, Optional
from agno.tools.reasoning import ReasoningTools
from enum import Enum


# Load environment variables
load_dotenv()

# --- Local Lead Generation Output Model Definitions ---
class PreviousRole(BaseModel):
    """A model to structure information about a contact's previous roles."""
    title: str = Field(..., description="The job title of the previous role.")
    company: str = Field(..., description="The company/business of the previous role.")
    duration: Optional[str] = Field(None, description="Duration in the role (e.g., '2019-2021' or '2 years').")

class EmploymentStatus(str, Enum):
    """Current employment status of a contact at the business."""
    CURRENT = "CURRENT"  # Verified within last 6 months
    LIKELY_CURRENT = "LIKELY_CURRENT"  # Evidence within 12 months
    UNCERTAIN = "UNCERTAIN"  # Data older than 12 months
    FORMER = "FORMER"  # Confirmed to have left

class VerificationRecency(str, Enum):
    """How recent the employment verification is."""
    RECENT = "RECENT"  # < 6 months
    MODERATE = "MODERATE"  # 6-12 months
    DATED = "DATED"  # > 12 months

class PhoneType(str, Enum):
    """Type of phone number found."""
    BUSINESS_MAIN = "BUSINESS_MAIN"  # Main business line
    BUSINESS_DIRECT = "BUSINESS_DIRECT"  # Direct business extension
    PERSONAL = "PERSONAL"  # Personal/mobile number
    UNKNOWN = "UNKNOWN"  # Type couldn't be determined

class EmailType(str, Enum):
    """Type of email address found."""
    DIRECT = "DIRECT"  # Personal work email (john.smith@company.com)
    GENERIC = "GENERIC"  # Generic role email (info@, contact@, sales@)
    PATTERN = "PATTERN"  # Email pattern detected (first.last@domain.com)
    NOT_FOUND = "NOT_FOUND"  # No email found, using fallback

class LocalContact(BaseModel):
    """Model for local business contact information suitable for lead generation."""
    name: str = Field(..., description="The full name of the contact.")
    title: str = Field(..., description="Current job title (e.g., 'Superintendent', 'General Manager', 'Owner').")
    business_name: str = Field(..., description="The name of the business where they work.")
    business_website: Optional[str] = Field(None, description="The business website URL.")
    phone: Optional[str] = Field(None, description="Contact phone number (business or direct).")
    phone_type: Optional[PhoneType] = Field(None, description="Type of phone number: 'BUSINESS_MAIN', 'BUSINESS_DIRECT', 'PERSONAL', or 'UNKNOWN'")
    email: str = Field(..., description="Contact email address. Always provided - either direct email or constructed pattern.")
    email_type: EmailType = Field(..., description="Type of email: 'DIRECT', 'GENERIC', 'PATTERN', or 'NOT_FOUND'")
    email_pattern: Optional[str] = Field(None, description="Common email pattern for the company (e.g., 'first.last@domain.com', 'flast@domain.com')")
    address: Optional[str] = Field(None, description="Business address or location.")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL if available.")
    years_in_position: Optional[str] = Field(None, description="How long they've been in current role.")
    employment_status: EmploymentStatus = Field(..., description="Current employment status: 'CURRENT', 'LIKELY_CURRENT', 'UNCERTAIN', 'FORMER'")
    last_verified_date: Optional[str] = Field(None, description="Date when employment was last verified (ISO format or 'YYYY-MM')")
    verification_recency: VerificationRecency = Field(..., description="How recent the verification is: 'RECENT' (<6mo), 'MODERATE' (6-12mo), 'DATED' (>12mo)")
    background_summary: str = Field(..., description="Brief summary of their role and responsibilities.")
    previous_roles: Optional[List[PreviousRole]] = Field(None, description="Previous positions if available.")
    source_urls: List[str] = Field(..., description="URLs where the information was found.")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0) based on data quality.")
    verification_notes: Optional[str] = Field(None, description="Notes about data verification.")

class LocalBusiness(BaseModel):
    """Structured information about a local business."""
    name: str = Field(..., description="Official business name.")
    address: Optional[str] = Field(None, description="Physical address of the business.")
    phone: Optional[str] = Field(None, description="Main business phone number.")
    website_url: Optional[str] = Field(None, description="Business website URL.")
    business_type: str = Field(..., description="Type of business (e.g., 'Golf Course', 'Restaurant', 'Retail').")
    description: str = Field(..., description="Brief description of what the business does.")
    services_offered: Optional[List[str]] = Field(None, description="Key services or products offered.")
    operating_hours: Optional[str] = Field(None, description="Business hours of operation.")
    years_established: Optional[int] = Field(None, description="Year the business was established.")
    employee_count_estimate: Optional[str] = Field(None, description="Estimated number of employees.")
    review_rating: Optional[float] = Field(None, description="Average review rating if available.")
    specialties: Optional[List[str]] = Field(None, description="Business specialties or unique offerings.")
    location_details: Optional[str] = Field(None, description="Additional location context (neighborhood, nearby landmarks).")

class SearchMetadata(BaseModel):
    """Metadata about the search process and methods used."""
    search_terms_used: List[str] = Field(..., description="Actual search queries executed.")
    sources_searched: List[str] = Field(..., description="Sources checked (e.g., 'Business Website', 'LinkedIn', 'Local Directories').")
    verification_methods: List[str] = Field(..., description="Methods used to verify information.")
    total_results_analyzed: int = Field(..., description="Number of search results analyzed.")
    job_titles_searched: List[str] = Field(..., description="Specific job titles searched for.")
    search_location: Optional[str] = Field(None, description="Geographic location if location-based search.")
    search_radius: Optional[str] = Field(None, description="Search radius if applicable.")
    email_pattern_detected: Optional[str] = Field(None, description="Company email pattern detected (e.g., 'first.last@domain.com')")
    emails_found_count: int = Field(0, description="Number of direct emails found vs constructed")
    challenges_encountered: Optional[List[str]] = Field(None, description="Any difficulties during search.")

class LocalLeadResults(BaseModel):
    """Structured output for local lead generation results."""
    # Business Section
    business: LocalBusiness = Field(..., description="Verified business information.")
    
    # Contacts Section
    contacts: List[LocalContact] = Field(..., description="List of contacts found at the business.")
    contacts_found: int = Field(..., description="Total number of contacts found.")
    
    # Metadata Section
    metadata: SearchMetadata = Field(..., description="Search process metadata.")
    search_confidence: str = Field(..., description="Overall confidence: 'HIGH', 'MEDIUM', or 'LOW'.")
    search_query: str = Field(..., description="Original search query.")

# Configuration
DEBUG_MODE = True

# Model-specific configuration
MODEL_CONFIGS = {
    # Anthropic models
    "anthropic/claude-3.5-sonnet": {"max_tokens": 65000, "use_json_mode": True},
    "anthropic/claude-3.5-sonnet:beta": {"max_tokens": 65000, "use_json_mode": True},
    "anthropic/claude-3-sonnet": {"max_tokens": 65000, "use_json_mode": True},
    "anthropic/claude-3-opus": {"max_tokens": 65000, "use_json_mode": True},
    "anthropic/claude-3-haiku": {"max_tokens": 65000, "use_json_mode": True},
    "anthropic/claude-sonnet-4": {"max_tokens": 65000, "use_json_mode": True},
    "anthropic/claude-opus-4": {"max_tokens": 65000, "use_json_mode": True},
    
    # OpenAI models
    "openai/gpt-4": {"max_tokens": 8192, "use_json_mode": True},
    "openai/gpt-4-turbo": {"max_tokens": 16384, "use_json_mode": True},
    "openai/gpt-4-turbo-preview": {"max_tokens": 16384, "use_json_mode": True},
    "openai/gpt-4o": {"max_tokens": 16384, "use_json_mode": True},
    "openai/gpt-4o-mini": {"max_tokens": 16384, "use_json_mode": True},
    "openai/gpt-3.5-turbo": {"max_tokens": 16384, "use_json_mode": True},
    
    # Google models
    "google/gemini-2.0-flash-exp": {"max_tokens": 8192, "use_json_mode": False},
    "google/gemini-2.5-pro": {"max_tokens": 65000, "use_json_mode": False},
    "google/gemini-1.5-pro": {"max_tokens": 8192, "use_json_mode": False},
    "google/gemini-1.5-flash": {"max_tokens": 8192, "use_json_mode": False},
    "google/gemini-pro": {"max_tokens": 8192, "use_json_mode": False},
    "google/gemini-pro-vision": {"max_tokens": 8192, "use_json_mode": False},
    
    # Meta models
    "meta-llama/llama-3.1-405b-instruct": {"max_tokens": 8192, "use_json_mode": True},
    "meta-llama/llama-3.1-70b-instruct": {"max_tokens": 8192, "use_json_mode": True},
    "meta-llama/llama-3.1-8b-instruct": {"max_tokens": 8192, "use_json_mode": True},
    
    # Mistral models
    "mistralai/mistral-large": {"max_tokens": 8192, "use_json_mode": True},
    "mistralai/mixtral-8x7b-instruct": {"max_tokens": 8192, "use_json_mode": True},
    "mistralai/mistral-7b-instruct": {"max_tokens": 8192, "use_json_mode": True},
    
    # Default fallback configuration
    "default": {"max_tokens": 8192, "use_json_mode": False}
}

# Dynamic model configuration
def get_model_config(model_id):
    """Get configuration for a specific model, with fallback to defaults."""
    return MODEL_CONFIGS.get(model_id, MODEL_CONFIGS["default"])

# Set your model here - can be overridden by command line argument or environment
DEFAULT_MODEL = "anthropic/claude-sonnet-4"
# Check for environment variable first, then command line arg, then default
MODEL_ID = os.getenv('DEFAULT_MODEL', DEFAULT_MODEL)
if len(sys.argv) > 1 and not sys.argv[0].endswith('gunicorn'):
    MODEL_ID = sys.argv[1]

# Get model-specific configuration
model_config = get_model_config(MODEL_ID)
MAX_TOKENS = model_config["max_tokens"]
USE_JSON_MODE = model_config["use_json_mode"]

print(f"🔧 Model Configuration for {MODEL_ID}:")
print(f"   - Max Tokens: {MAX_TOKENS}")
print(f"   - JSON Mode: {USE_JSON_MODE}")
print(f"   - Usage: python exa-local.py [model_id] (e.g., python exa-local.py google/gemini-2.5-pro)\n")

# Validate required environment variables
required_env_vars = ["OPENROUTER_API_KEY", "EXA_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# --- Local Lead Generation Agent Instructions ---
AGENT_INSTRUCTIONS = f"""
You are an expert local business lead generation specialist focused on finding key contacts at local businesses.

**MISSION: Find practical contacts and decision-makers at local businesses who match the search criteria.**

## AVAILABLE TOOLS
- **search_exa**: Search for local businesses, contacts, and web content
- **get_contents**: Crawl specific URLs to extract detailed information
- **find_similar**: Find pages similar to a given URL
- **exa_answer**: Get AI-powered summaries about businesses or people

## CRITICAL WORKFLOW

### STEP 0: Parse Input
First, identify what's in the query:
- **Domain** (e.g., "pebblebeach.com", "olivegarden.com") → Start with business research
- **Business name + location** (e.g., "Joe's Pizza in Brooklyn") → Search with location context
- **Business type + area** (e.g., "golf courses near 94062") → Area-based search

### PHASE 1: Deep Business Understanding
**USE get_contents on the domain to understand:**
1. What type of business is this? (golf course, restaurant, retail, service)
2. What services do they offer? (menu, services list, amenities)
3. Where are they located? (address, service area)
4. How big is the operation? (multiple locations, staff size indicators)

**Also search_exa for:**
- "[Business name] staff directory"
- "[Business name] management team"
- "[Business name] contact information"
- "[Business name] about us team"

### PHASE 2: Context-Aware Contact Search
**Based on business type, search for relevant roles:**

For Golf Courses:
- "Superintendent", "Head Groundskeeper", "Golf Course Manager"
- "Director of Golf", "Head Professional", "General Manager"
- "Membership Director", "F&B Manager"

For Restaurants:
- "General Manager", "Restaurant Manager", "Owner"
- "Head Chef", "Executive Chef", "Kitchen Manager"
- "Bar Manager", "Events Manager"

For Retail/Service Businesses:
- "Owner", "Store Manager", "General Manager"
- "Operations Manager", "Service Manager"
- "Sales Manager", "District Manager"

For Hotels/Hospitality:
- "General Manager", "Hotel Manager"
- "F&B Director", "Front Desk Manager"
- "Sales Director", "Events Manager"

**CRITICAL: Focus on finding practical contact information (phone, email, address).**

Use these search patterns:
1. search_exa: "[Business name] [Role] contact"
2. search_exa: "[Business name] staff directory"
3. get_contents on business's /about, /team, or /contact pages
4. search_exa: "[Business domain] management team"
5. search_exa: "email @[domain]" to find email patterns

Additional verification searches:
6. search_exa: "[Contact name] [Company] 2024 2025" for recent mentions
7. search_exa: "[Company] announces new [role title]" to check for replacements
8. search_exa: "[Contact name] linkedin [Company]" for profile updates
9. get_contents on company news/blog pages for recent mentions
10. search_exa: "[Contact name] former [Company]" to check if they've left

Email-specific searches (CRITICAL - always attempt these):
11. search_exa: "[Contact name] email @[domain]" for direct email
12. search_exa: "site:[domain] email contact" for email patterns
13. search_exa: "[Business name] staff email addresses" for directories
14. get_contents on /contact, /about, /team pages looking for emails
15. search_exa: "[domain] email format" to find company patterns

### Email Pattern Detection Strategy:
1. **Collect Examples**: Find 3-5 employee emails from the company
2. **Identify Pattern**: Common patterns include:
   - first.last@domain.com (most common - 60% of companies)
   - firstlast@domain.com (20% of companies)
   - flast@domain.com (first initial + last - 10%)
   - first@domain.com (5%)
   - last.first@domain.com (rare)
3. **Verify Pattern**: Test pattern consistency across found emails
4. **Apply Pattern**: Use detected pattern for contacts without direct emails
5. **Document Pattern**: Store the detected pattern in email_pattern field

### PHASE 3: Verify & Extract Contact Info
For each contact found:
- Extract full name and exact title
- **CRITICAL: Verify current employment status:**
  - Check if they appear on current website staff pages
  - Search for "[Name] still at [Company]" or "[Name] left [Company]"
  - Look for recent LinkedIn activity at the company
  - Check publication/mention dates to assess recency
  - Search for successor announcements if data is old
  - Note the date of the most recent verification
- Find phone numbers and classify type:
  - BUSINESS_MAIN: Main business number shared by multiple staff
  - BUSINESS_DIRECT: Direct extension or department line
  - PERSONAL: Mobile/cell numbers found in bios or personal profiles
  - UNKNOWN: When source doesn't clarify type
- **CRITICAL: Find or construct email addresses:**
  - Search for direct email (best case)
  - Look for company email patterns (first.last@, flast@, etc.)
  - Check staff directories, contact pages, press releases
  - If no direct email found, detect pattern from other employees
  - **ALWAYS provide an email using these fallbacks:**
    - Pattern-based: If you find john.doe@company.com, construct jane.smith@company.com
    - Generic role-based: info@domain.com, contact@domain.com
    - Domain-based guess: first.last@domain.com (most common pattern)
  - **Example Pattern Detection:**
    - Found: sarah.jones@deadhorselake.com, mike.wilson@deadhorselake.com
    - Pattern detected: first.last@domain.com
    - Applied to "Travis Hopkins" → travis.hopkins@deadhorselake.com (type: PATTERN)
  - Classify email type (DIRECT, GENERIC, PATTERN, NOT_FOUND)
- Note their specific responsibilities
- **Classify employment status based on evidence recency:**
  - CURRENT: Verified within last 6 months
  - LIKELY_CURRENT: Evidence within 12 months
  - UNCERTAIN: Data older than 12 months
  - FORMER: Confirmed to have left
- Get business address if not already found

### PHASE 4: Quality Control
- Confidence scoring based on employment recency AND data quality:
  - Current website listing + recent activity (0.95-1.0)
  - Multiple recent sources (<6 months) (0.85-0.95)
  - LinkedIn active + business site match (0.8-0.9)
  - Single source 6-12 months old (0.6-0.8)
  - Data older than 12 months (0.4-0.6)
  - Only historical data available (0.2-0.4)
  - Confirmed former employee (0.1-0.2)

## OUTPUT FORMAT
Return LocalLeadResults with:

1. **Business Section** - Complete LocalBusiness info:
   - Business type and services offered
   - Physical address and main phone
   - Operating hours if available
   - Years in business and size

2. **Contacts Section** - Relevant LocalContact list:
   - Practical job titles (not just C-suite)
   - Direct contact information when available
   - Their specific role at the business
   - How to reach them
   - **Employment status (CURRENT/LIKELY_CURRENT/UNCERTAIN/FORMER)**
   - **Last verified date and verification recency**
   - **Phone type classification (BUSINESS_MAIN/BUSINESS_DIRECT/PERSONAL/UNKNOWN)**
   - **Email ALWAYS provided with type (DIRECT/GENERIC/PATTERN/NOT_FOUND)**
   - **Email pattern detected for the company (if found)**

3. **Metadata Section** - Search process details:
   - Job titles searched based on business type
   - Sources used (website, directories, etc.)
   - Contact information found vs. missing

## EXAMPLES

**"superintendent at pebblebeach.com"**
→ First understand: World-famous golf course
→ Find golf course superintendent with contact info
→ Verify if still employed (check recent mentions, website listing)
→ Set employment status based on verification recency

**"general manager at olivegarden.com in San Antonio"**
→ First understand: Chain restaurant, need specific location
→ Find GM at San Antonio locations

**"owner of joes-plumbing.com"**
→ First understand: Local service business
→ Find owner/operator with business contact info

**"head chef at frenchlaundry.com"**
→ First understand: High-end restaurant
→ Find executive chef and kitchen leadership

**Remember: The goal is actionable contact information for sales outreach or business development, not just names.**
"""

# Initialize the local lead generation agent
agent = Agent(
    name="Local Lead Generation Agent",
    model=OpenRouter(
        id=MODEL_ID,
        max_tokens=MAX_TOKENS,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        # request_params={"usage": True},
    ),
    response_model=LocalLeadResults,  # Now returns local business contacts
    tools=[
        ExaTools(
            text_length_limit=4000,
            num_results=10,  # Balanced for speed
            highlights=True,
            summary=True,
            show_results=True,
            use_autoprompt=True
        ),
        ReasoningTools(
            add_instructions=True, 
            think=True, 
            analyze=True
        ),
    ],
    instructions=AGENT_INSTRUCTIONS,
    markdown=True,
    debug_mode=DEBUG_MODE,
    add_datetime_to_instructions=True,
    show_tool_calls=True,
    use_json_mode=USE_JSON_MODE
)

# Example queries demonstrating various local business scenarios
if __name__ == "__main__":
    # Example queries to test:
    example_queries = [
        "superintendent + general leadership at oakridgecountryclub.org",  # Golf course superintendent
        "general manager at golfknox.com",  # Entertainment venue manager
        "leadership/superintendent/manager of deadhorselake.com in knoxville",  # Local service business owner
        "head chef at frenchlaundry.com",  # Restaurant executive chef
        "manager at wholefoodsmarket.com in Austin",  # Location-specific search
        "director of golf at augustanational.com",  # Golf course leadership
        "superintendent at torrey-pines.com",  # Another golf course example
    ]
    
    # Run the query specified or default
    query = example_queries[0]  # Change index to test different queries
    print(f"\n🔍 Searching for: {query}\n")
    agent.print_response(query)

