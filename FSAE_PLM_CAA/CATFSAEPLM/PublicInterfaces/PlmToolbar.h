#ifndef PlmToolbar_H
#define PlmToolbar_H

#include "CATWorkbench.h"
#include "CATString.h"

/**
 * FSAE-PLM Workbench - creates the custom toolbar inside CATIA V5.
 *
 * Registers a new workbench named "FSAE-PLM" with a toolbar containing
 * buttons for all PLM operations: Login, Search, Checkout, Checkin,
 * Publish, Sync Properties, Create Part.
 */
class PlmWorkbench : public CATWorkbench
{
    CATDeclareClass;

public:
    PlmWorkbench();
    virtual ~PlmWorkbench();

    // CATIWorkbench interface
    CATCmdContainer* CreateCommands();

protected:
    // Creates the toolbar and its command headers
    void CreateToolbar();
};

#endif
