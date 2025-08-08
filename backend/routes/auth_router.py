import logging

from fastapi import APIRouter

from common.error_messages import get_error_message
from common.exceptions import CustomAgentException, ErrorCode
from common.response import RestResponse
from entities.bo import LoginRequest, WalletLoginRequest, RefreshTokenRequest
from entities.dto import LoginResponse, NonceResponse, WalletLoginResponse, TokenResponse
from services import auth_service

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/api/auth/login", response_model=RestResponse[LoginResponse], summary="User login")
async def login(request: LoginRequest):
    """
    User login endpoint

    - **username**: Username or email for login
    - **password**: Password for login
    """
    try:
        result = await auth_service.login(request)
        return RestResponse(data=result)
    except CustomAgentException as e:
        logger.error(f"Error in user login: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in user login: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )

@router.post("/api/auth/wallet/nonce", response_model=RestResponse[NonceResponse])
async def get_nonce(wallet_address: str):
    """
    Get nonce for wallet signature

    - **wallet_address**: Ethereum wallet address
    """
    try:
        result = await auth_service.get_wallet_nonce(wallet_address)
        return RestResponse(data=result)
    except CustomAgentException as e:
        logger.error(f"Error getting nonce for wallet: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting nonce: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.post("/api/auth/wallet/login", response_model=RestResponse[WalletLoginResponse])
async def wallet_login(request: WalletLoginRequest):
    """
    Login or register with wallet
    
    This endpoint allows users to authenticate using their blockchain wallet.
    The user signs a message containing a nonce, and the signature is verified.
    
    Parameters:
        - wallet_address: The wallet address
        - signature: The signature of the message
        - chain_type: The blockchain type (ethereum, solana, etc.), defaults to ethereum
        
    Returns:
        - access_token: JWT access token
        - refresh_token: JWT refresh token for obtaining new access tokens
        - user: User information
        - is_new_user: Whether this is a new user
        - access_token_expires_in: Access token expiration time in seconds
        - refresh_token_expires_in: Refresh token expiration time in seconds
    """
    try:
        result = await auth_service.wallet_login(request)
        return RestResponse(data=result)
    except CustomAgentException as e:
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Error in wallet login: {e}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.post("/api/auth/refresh", response_model=RestResponse[TokenResponse])
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    try:
        result = await auth_service.refresh_token(request.refresh_token)
        return RestResponse(data=result)
    except CustomAgentException as e:
        logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error refreshing token: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )
