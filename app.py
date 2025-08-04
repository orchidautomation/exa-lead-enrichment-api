"""
Exa Lead Enrichment API - Simplified
AI-powered contact enrichment for business domains
"""
import os
import logging
import uuid
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Flask configuration
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS for all endpoints
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Lazy load the agent to avoid import issues
    agent = None
    
    def get_agent():
        """Lazy load the agent on first use."""
        nonlocal agent
        if agent is None:
            logger.info("Initializing agent for first time...")
            from exa_local import agent as exa_agent
            agent = exa_agent
            logger.info("Agent initialized successfully")
        return agent
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint.
        Returns the status of required API keys.
        """
        try:
            # Check required environment variables
            openrouter_key = bool(os.getenv('OPENROUTER_API_KEY'))
            exa_key = bool(os.getenv('EXA_API_KEY'))
            
            # Overall health
            all_keys_present = openrouter_key and exa_key
            status = "healthy" if all_keys_present else "degraded"
            status_code = 200 if all_keys_present else 503
            
            return jsonify({
                "status": status,
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "openrouter_api": "configured" if openrouter_key else "missing",
                    "exa_api": "configured" if exa_key else "missing"
                }
            }), status_code
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/enrich', methods=['POST'])
    def enrich():
        """
        Main enrichment endpoint.
        Finds contacts and business information for a given query.
        
        Expected JSON payload:
        {
            "query": "superintendent at pebblebeach.com"
        }
        
        Returns enriched contact and business information.
        """
        try:
            # Parse request
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({
                    "error": "Invalid request",
                    "detail": "Missing 'query' field"
                }), 400
            
            query = data['query']
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            logger.info(f"Enrichment request {request_id}: {query}")
            
            # Run the agent
            try:
                logger.info(f"Getting agent instance...")
                agent = get_agent()
                logger.info(f"Running agent with query: {query}")
                results = agent.run(query)
                logger.info(f"Agent run completed")
                
                # Convert Pydantic model to dict
                results_dict = results.model_dump() if hasattr(results, 'model_dump') else results.dict()
                logger.info(f"Results converted to dict")
                
                processing_time = time.time() - start_time
                logger.info(f"Request {request_id} completed in {processing_time:.2f}s")
                
                return jsonify({
                    "request_id": request_id,
                    "query": query,
                    "status": "success",
                    "processing_time": processing_time,
                    "results": results_dict
                })
                
            except Exception as e:
                logger.error(f"Agent error for {request_id}: {str(e)}")
                processing_time = time.time() - start_time
                
                return jsonify({
                    "request_id": request_id,
                    "query": query,
                    "status": "error",
                    "processing_time": processing_time,
                    "error": str(e)
                }), 500
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return jsonify({
                "error": "Invalid request",
                "detail": str(e)
            }), 400
    
    @app.route('/test', methods=['GET', 'POST'])
    def test_endpoint():
        """Simple test endpoint to verify API is working."""
        return jsonify({
            "status": "ok",
            "message": "Test endpoint working",
            "timestamp": datetime.now().isoformat(),
            "method": request.method
        })
    
    @app.route('/')
    def index():
        """API information endpoint."""
        return jsonify({
            "name": "Exa Lead Enrichment API",
            "version": "1.0.0",
            "description": "AI-powered contact enrichment for business domains",
            "endpoints": {
                "enrich": {
                    "path": "/enrich",
                    "method": "POST",
                    "description": "Enrich business domain with contact information",
                    "example_request": {
                        "query": "superintendent at pebblebeach.com"
                    }
                },
                "health": {
                    "path": "/health",
                    "method": "GET",
                    "description": "Check API health and service status"
                }
            },
            "example_queries": [
                "superintendent at pebblebeach.com",
                "general manager at olivegarden.com in San Antonio",
                "owner of joes-plumbing.com",
                "head chef at frenchlaundry.com"
            ]
        })
    
    logger.info("Exa Lead Enrichment API initialized")
    return app


if __name__ == '__main__':
    # Validate environment
    required_vars = ['OPENROUTER_API_KEY', 'EXA_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set these in your .env file or environment")
        exit(1)
    
    # Create and run app
    app = create_app()
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))  # Different port from mapper API
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Exa Lead Enrichment API on {host}:{port}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )