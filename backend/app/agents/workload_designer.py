import json
import requests
from config import TARGET_APP_URL
from agents.llm_client import llm_client

class WorkloadDesigner:
    def design_workload(self) -> dict:
        # Default fallback workload configuration
        fallback_workload = {
            "browse_products": 5,
            "get_recommendations": 3,
            "view_orders": 2,
            "checkout_process": 1,
            "check_db_status": 1
        }
        
        try:
            # Attempt to fetch target app's OpenAPI spec
            openapi_url = f"{TARGET_APP_URL}/openapi.json"
            res = requests.get(openapi_url, timeout=3)
            if res.status_code == 200:
                spec = res.json()
                paths = list(spec.get("paths", {}).keys())
                
                # If LLM is available, ask it to design weighted endpoints
                if llm_client.model:
                    prompt = f"""
                    Analyze the following OpenAPI endpoints and design a realistic user journey workload.
                    Assign weights (relative frequency of calls) to each route, summing up to 12.
                    Endpoints: {json.dumps(paths)}
                    
                    Return a JSON object matching this structure:
                    {{
                        "route_name_or_matching_locust_task": weight_integer
                    }}
                    """
                    llm_response = llm_client.generate_json(prompt)
                    designed = json.loads(llm_response)
                    if isinstance(designed, dict) and len(designed) > 0:
                        return designed
        except Exception as e:
            print(f"Workload design failed, using default fallback: {e}")
            
        return fallback_workload

workload_designer = WorkloadDesigner()
