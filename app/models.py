from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key= True)
    email = Column(String(200), nullable= False, unique= True, index= True)
    hashed_password = Column(String(200), nullable= False)
    is_active = Column(Boolean, nullable= False, server_default= "true")
    created_at = Column(DateTime(timezone= True),
                        server_default= func.now(),
                        nullable= False)
    api_keys = relationship("ApiKey", back_populates= "user")
    short_links = relationship("ShortLink", back_populates= "user")
    

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable= False)
    key_hash = Column(String(255), nullable= False)
    prefix = Column(String(20), nullable= False, index= True)
    is_active = Column(Boolean, nullable= False, server_default= "true")
    created_at = Column(DateTime(timezone= True),
                        server_default= func.now(),
                        nullable= False)
    user = relationship("User", back_populates= "api_keys")
    


class ShortLink(Base):
    __tablename__ = "short_links"
    id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable= False)
    original_url = Column(Text, nullable= False)
    short_code = Column(String(20), 
                        unique= True, 
                        index= True,
                        nullable= False
                        )
    password_hash = Column(String(200), nullable= True)
    expires_at = Column(DateTime(timezone=True), nullable= True)
    redirect_type = Column(Integer, nullable= False, default = 302)
    is_active = Column(Boolean, nullable= False, server_default= "true")
    created_at = Column(DateTime(timezone= True),
                        server_default= func.now(),
                        nullable= False)
    
    updated_at = Column(
                DateTime(timezone= True),
                server_default= func.now(),
                onupdate=func.now(),
                nullable= False)
    click_count = Column(Integer, nullable=False, default=0)
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates= "short_links")
    visit_analytics = relationship("VisitAnalytics", back_populates="short_link")



class VisitAnalytics(Base):
    __tablename__ = "visit_analytics"
    id = Column(Integer, primary_key=True)
    short_link_id = Column(Integer, ForeignKey("short_links.id"))
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
        )
    ip = Column(String)
    user_agent = Column(String)
    referrer = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    short_link = relationship("ShortLink", back_populates= "visit_analytics")