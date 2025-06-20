import openai
import json
import re
import os
from typing import Dict, List, Optional
from config import Config

class JobAnalyzer:
    """Analyzes job descriptions to extract keywords, requirements, and optimization insights"""
    
    def __init__(self, api_key: str = None):
        # Set the API key
        api_key = api_key or Config.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client with proper error handling
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            # Fallback: try setting the API key globally (for older versions)
            openai.api_key = api_key
            self.client = None
    
    def _make_openai_request(self, messages, temperature=0.3, max_tokens=1500, model="gpt-3.5-turbo"):
        """Make OpenAI API request with fallback for different library versions"""
        
        try:
            if self.client:
                # New OpenAI library (v1.0+)
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # Fallback for older versions
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            raise e
    
    def analyze_job_description(self, job_description: str) -> Dict[str, any]:
        """
        Comprehensive analysis of job description
        
        Returns:
            Dict containing:
            - keywords: extracted keywords with importance scores
            - requirements: categorized requirements
            - skills: technical and soft skills
            - experience_level: required experience
            - industry: detected industry
            - company_culture: cultural keywords
            - success: boolean
            - error: error message if failed
        """
        
        try:
            # Primary analysis prompt
            analysis_prompt = f"""
            Analyze the following job description and extract detailed information in JSON format:

            Job Description:
            {job_description}

            Please provide a comprehensive analysis in the following JSON structure:
            {{
                "keywords": {{
                    "high_priority": ["keyword1", "keyword2", ...],
                    "medium_priority": ["keyword3", "keyword4", ...],
                    "low_priority": ["keyword5", "keyword6", ...]
                }},
                "requirements": {{
                    "technical_skills": ["skill1", "skill2", ...],
                    "soft_skills": ["skill1", "skill2", ...],
                    "education": ["requirement1", "requirement2", ...],
                    "experience": ["requirement1", "requirement2", ...],
                    "certifications": ["cert1", "cert2", ...]
                }},
                "experience_level": "entry/mid/senior/executive",
                "industry": "detected_industry",
                "company_culture": ["culture_keyword1", "culture_keyword2", ...],
                "job_type": "full-time/part-time/contract/remote/hybrid",
                "salary_indicators": ["any salary or compensation mentions"],
                "location_requirements": ["location requirements if any"]
            }}

            Focus on:
            1. Technical keywords that should appear in resume/cover letter
            2. Action verbs and industry-specific terminology
            3. Required vs preferred qualifications
            4. Company values and culture indicators
            """

            response = self._make_openai_request(
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst specializing in job description analysis. Provide accurate, detailed analysis in valid JSON format."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON response
            analysis_text = response
            analysis_data = self._extract_json_from_response(analysis_text)
            
            if not analysis_data:
                return {'success': False, 'error': 'Failed to parse analysis response'}
            
            # Add additional processing
            analysis_data['all_keywords'] = self._flatten_keywords(analysis_data.get('keywords', {}))
            analysis_data['keyword_density'] = self._calculate_keyword_density(job_description, analysis_data['all_keywords'])
            
            return {
                'success': True,
                'analysis': analysis_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Job analysis failed: {str(e)}'
            }
    
    def extract_optimization_insights(self, job_description: str, resume_text: str, cover_letter_text: str) -> Dict[str, any]:
        """
        Generate specific optimization recommendations
        """
        
        try:
            optimization_prompt = f"""
            Analyze the job description against the current resume and cover letter to provide specific optimization recommendations:

            JOB DESCRIPTION:
            {job_description}

            CURRENT RESUME:
            {resume_text}

            CURRENT COVER LETTER:
            {cover_letter_text}

            Provide optimization insights in JSON format:
            {{
                "resume_gaps": ["missing keyword/skill 1", "missing keyword/skill 2", ...],
                "cover_letter_gaps": ["missing element 1", "missing element 2", ...],
                "keyword_opportunities": ["keyword to add 1", "keyword to add 2", ...],
                "experience_matching": {{
                    "strong_matches": ["experience 1", "experience 2", ...],
                    "weak_matches": ["experience 1", "experience 2", ...],
                    "missing_experiences": ["missing 1", "missing 2", ...]
                }},
                "ats_recommendations": ["recommendation 1", "recommendation 2", ...],
                "priority_actions": ["action 1", "action 2", ...]
            }}
            """

            response = self._make_openai_request(
                messages=[
                    {"role": "system", "content": "You are an expert resume optimizer. Provide specific, actionable recommendations."},
                    {"role": "user", "content": optimization_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            insights_text = response
            insights_data = self._extract_json_from_response(insights_text)
            
            return {
                'success': True,
                'insights': insights_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Optimization analysis failed: {str(e)}'
            }
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract JSON from OpenAI response, handling various formats"""
        
        try:
            # Try direct JSON parsing
            return json.loads(response_text)
        except:
            pass
        
        # Try to extract JSON from code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to find JSON-like content
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None
    
    def _flatten_keywords(self, keywords_dict: Dict) -> List[str]:
        """Flatten keywords from priority categories into single list"""
        
        all_keywords = []
        for priority_level, keyword_list in keywords_dict.items():
            if isinstance(keyword_list, list):
                all_keywords.extend(keyword_list)
        
        return list(set(all_keywords))  # Remove duplicates
    
    def _calculate_keyword_density(self, text: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density in the text"""
        
        text_lower = text.lower()
        word_count = len(text.split())
        
        density = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            density[keyword] = (count / word_count) * 100 if word_count > 0 else 0
        
        return density
    
    def get_industry_specific_keywords(self, industry: str) -> List[str]:
        """Get additional industry-specific keywords"""
        
        industry_keywords = {
            'technology': ['agile', 'scrum', 'devops', 'ci/cd', 'microservices', 'api', 'cloud', 'aws', 'azure'],
            'finance': ['compliance', 'risk management', 'sox', 'financial modeling', 'bloomberg', 'excel'],
            'healthcare': ['hipaa', 'clinical', 'patient care', 'ehr', 'medical records', 'compliance'],
            'marketing': ['seo', 'sem', 'google analytics', 'social media', 'content marketing', 'brand'],
            'sales': ['crm', 'salesforce', 'lead generation', 'quota', 'pipeline', 'b2b', 'b2c']
        }
        
        return industry_keywords.get(industry.lower(), [])