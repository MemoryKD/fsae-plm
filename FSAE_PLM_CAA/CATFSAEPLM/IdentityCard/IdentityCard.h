#ifndef CATFSAEPLM_IdentityCard_H
#define CATFSAEPLM_IdentityCard_H

#include "CATBaseUnknown.h"

/**
 * Framework Identity Card
 * Declares which other CAA frameworks this framework depends on.
 */
class CATFSAEPLMIdentityCard : public CATBaseUnknown
{
    CATDeclareClass;

public:
    CATFSAEPLMIdentityCard();
    virtual ~CATFSAEPLMIdentityCard();
};

#endif
