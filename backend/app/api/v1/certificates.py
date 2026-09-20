"""Course-completion certificate endpoints.

A learner becomes eligible once every video is completed and every quiz
attached to the course is passed. Until then the eligibility endpoint
reports the missing pieces and the download endpoint returns 422.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.services.certificate_service import CertificateService

router = APIRouter(tags=["certificates"])


@router.get(
    "/courses/{course_id}/certificate/eligibility",
    summary="Check whether the current user can download the course certificate",
)
def get_certificate_eligibility(
    course_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    eligibility = CertificateService(db).get_eligibility(
        user=current_user, course_id=course_id
    )
    return eligibility.to_dict()


@router.get(
    "/courses/{course_id}/certificate",
    summary="Download the course-completion PDF certificate",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "PDF certificate",
            "content": {"application/pdf": {}},
        },
        422: {"description": "Course not completed yet"},
    },
)
def download_certificate(
    course_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    pdf_bytes, filename, _ = CertificateService(db).build_pdf(
        user=current_user, course_id=course_id
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(pdf_bytes)),
        "Cache-Control": "no-store",
    }
    return StreamingResponse(
        iter([pdf_bytes]), media_type="application/pdf", headers=headers
    )
