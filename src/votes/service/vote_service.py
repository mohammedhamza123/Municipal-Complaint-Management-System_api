"""
Vote service (Application Layer)
"""
from typing import List
from sqlalchemy.orm import Session
from src.votes.repository.vote_repository import VoteRepository
from src.votes.schema.vote import VoteCreate
from src.core.exceptions import DuplicateError, NotFoundError
from src.votes.model.vote import Vote


class VoteService:
    """Service for vote business logic"""
    
    def __init__(self, db: Session):
        self.repository = VoteRepository(db)
    
    def create_vote(self, vote_data: VoteCreate, user_id: int) -> Vote:
        """Create a new vote"""
        # Check if user already voted on this issue
        existing_vote = self.repository.get_by_user_and_issue(user_id, vote_data.issue_id)
        if existing_vote:
            # Update existing vote
            return self.repository.update(existing_vote.id, {"is_upvote": vote_data.is_upvote})
        
        vote_dict = vote_data.model_dump()
        vote_dict["user_id"] = user_id
        return self.repository.create(vote_dict)
    
    def get_vote(self, vote_id: int) -> Vote:
        """Get vote by ID"""
        vote = self.repository.get_by_id(vote_id)
        if not vote:
            raise NotFoundError("Vote", str(vote_id))
        return vote
    
    def get_issue_votes(self, issue_id: int) -> List[Vote]:
        """Get all votes for an issue"""
        return self.repository.get_by_issue(issue_id)
    
    def delete_vote(self, vote_id: int) -> bool:
        """Delete vote"""
        return self.repository.delete(vote_id)

