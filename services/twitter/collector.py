from datetime import datetime, timedelta
import tweepy
from sqlalchemy.orm import Session
from models.user import User
from models.engagement import Engagement
from core.pult.processor import PULTProcessor

class TwitterDataCollector:
    def __init__(self, db: Session):
        self.db = db
        self.pult_processor = PULTProcessor(db)
        
    async def collect_user_data(self, user_id: int):
        """Collect and process user's Twitter data"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.access_token:
            raise ValueError("User not found or not authenticated")
            
        # Initialize Twitter client
        client = tweepy.Client(user.access_token)
        
        try:
            # Get user's recent likes
            likes = await self._get_user_likes(client)
            
            # Get user's recent retweets
            retweets = await self._get_user_retweets(client)
            
            # Get user's recent replies
            replies = await self._get_user_replies(client)
            
            # Process and store engagements
            await self._store_engagements(user.id, likes, retweets, replies)
            
            # Update PULT score
            pult_score = self.pult_processor.process_user_data(user.id)
            
            return {
                "success": True,
                "engagements_processed": len(likes) + len(retweets) + len(replies),
                "pult_score": pult_score
            }
            
        except Exception as e:
            raise ValueError(f"Error collecting Twitter data: {str(e)}")
    
    async def _get_user_likes(self, client):
        """Fetch user's recent likes"""
        try:
            likes = client.get_liked_tweets(max_results=100)
            return [{"id": tweet.id, "type": "like", "created_at": tweet.created_at} 
                   for tweet in (likes.data or [])]
        except:
            return []
    
    async def _get_user_retweets(self, client):
        """Fetch user's recent retweets"""
        try:
            # Get user's tweets that are retweets
            tweets = client.get_users_tweets(max_results=100)
            retweets = [tweet for tweet in (tweets.data or []) if hasattr(tweet, 'referenced_tweets')]
            return [{"id": tweet.id, "type": "retweet", "created_at": tweet.created_at} 
                   for tweet in retweets]
        except:
            return []
    
    async def _get_user_replies(self, client):
        """Fetch user's recent replies"""
        try:
            # Get user's tweets that are replies
            tweets = client.get_users_tweets(max_results=100)
            replies = [tweet for tweet in (tweets.data or []) if tweet.in_reply_to_user_id]
            return [{"id": tweet.id, "type": "reply", "created_at": tweet.created_at} 
                   for tweet in replies]
        except:
            return []
    
    async def _store_engagements(self, user_id: int, likes, retweets, replies):
        """Store all engagements in database"""
        all_engagements = []
        
        # Process all engagement types
        for engagement_list in [likes, retweets, replies]:
            for eng in engagement_list:
                engagement = Engagement(
                    user_id=user_id,
                    tweet_id=str(eng["id"]),
                    engagement_type=eng["type"],
                    created_at=eng["created_at"]
                )
                all_engagements.append(engagement)
        
        # Bulk insert engagements
        self.db.bulk_save_objects(all_engagements)
        self.db.commit() 