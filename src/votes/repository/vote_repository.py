"""
Vote repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.votes.model.vote import Vote
from src.core.exceptions import NotFoundError


class VoteRepository:
    """Repository for vote data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, vote_data: dict) -> Vote:
        """Create a new vote"""
        vote = Vote(**vote_data)
        self.db.add(vote)
        self.db.commit()
        self.db.refresh(vote)
        return vote
    
    def get_by_id(self, vote_id: int) -> Optional[Vote]:
        """Get vote by ID"""
        return self.db.query(Vote).filter(Vote.id == vote_id).first()
    
    def get_by_user_and_issue(self, user_id: int, issue_id: int) -> Optional[Vote]:
        """Get vote by user and issue"""
        return self.db.query(Vote).filter(
            and_(Vote.user_id == user_id, Vote.issue_id == issue_id)
        ).first()
    
    def get_by_issue(self, issue_id: int) -> List[Vote]:
        """Get all votes for an issue"""
        return self.db.query(Vote).filter(Vote.issue_id == issue_id).all()
    
    def update(self, vote_id: int, vote_data: dict) -> Vote:
        """Update vote"""
        vote = self.get_by_id(vote_id)
        if not vote:
            raise NotFoundError("Vote", str(vote_id))
        
        for key, value in vote_data.items():
            setattr(vote, key, value)
        
        self.db.commit()
        self.db.refresh(vote)
        return vote
    
    def delete(self, vote_id: int) -> bool:
        """Delete vote"""
        vote = self.get_by_id(vote_id)
        if not vote:
            raise NotFoundError("Vote", str(vote_id))
        
        self.db.delete(vote)
        self.db.commit()
        return True




























