"""
Certificate Generation Exceptions
"""

class CertificateError(Exception):
    """Base Exception for all cert-related errors"""
    pass

class LoaderError(CertificateError):
    """
    Raised CSV/Excel Load Fails.

    Examples:
       -file not found
       -invalid format
       -missing colums 
       -Null values 
       -invalid data types
    """

    pass

class TemplateFormatError(CertificateError):
    """
    Raised Template provided in wrong format

    Examples:
    -files not in png/svg 
    -png file corrupted
    -svg invalid xml
    -template too small (<800x600)
    """
    pass

class OverlayError(CertificateError):
    """
    Raised when text overlay on image fails.

    eg:

    -font file not found(even after fallback)
    -PIL cannot open img
    -COordinates out of bounds 
    -image format error
    -text rendering error

    """
    pass

class TemplateNotFoundError(CertificateError):
    """
    Raised when template PNG/SVG file not found.

    Examples:
    - file not found at exact path
    - not found in fallback locations (./, events/sparkverse/)
    """

    pass


class InvalidParticipationError(CertificateError):
    """
    Raised when Participant datas Validation fails.

    eg:
    -Name is empty or too long
    -Team Name is empty or too long (>100 Characters)
    -Email Doesnt contains @
    -invalid characters in name/team
    """

    pass


# Alias for spec compliance - plan.md uses InvalidParticipantError
class InvalidParticipantError(InvalidParticipationError):
    """Alias for InvalidParticipationError (spec name)."""

    pass


class OutputError(CertificateError):
    """
    Raised When Cannot write output file.
    eg:
    -Permission denied on output directory
    -Disk Full
    -Op path is invalid
    -cannot Create Dir 

    """
    pass