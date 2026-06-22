"""
Vote router (Presentation Layer)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependencies import DatabaseDep
from src.votes.service.vote_service import VoteService
from src.votes.schema.vote import Vote, VoteCreate


router = APIRouter(prefix="/votes", tags=["votes"])


@router.post("/", response_model=Vote, status_code=status.HTTP_201_CREATED)
def create_vote(vote: VoteCreate, user_id: int, db: DatabaseDep):
    """Create or update a vote"""
    service = VoteService(db)
    return service.create_vote(vote, user_id)


@router.get("/issue/{issue_id}", response_model=List[Vote])
def get_issue_votes(issue_id: int, db: DatabaseDep):
    """Get all votes for an issue"""
    service = VoteService(db)
    return service.get_issue_votes(issue_id)


@router.delete("/{vote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vote(vote_id: int, db: DatabaseDep):
    """Delete vote"""
    service = VoteService(db)
    service.delete_vote(vote_id)
    return None




























