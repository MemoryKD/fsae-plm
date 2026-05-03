#ifndef PlmCommands_H
#define PlmCommands_H

#include "CATCommand.h"
#include "CATString.h"
#include "CATUnicodeString.h"

class PlmBridge;

/**
 * Base command for all PLM toolbar buttons.
 * Each command handles one toolbar button click.
 */
class PlmBaseCommand : public CATCommand
{
    CATDeclareClass;

public:
    PlmBaseCommand(const CATString& commandId, PlmBridge* bridge);
    virtual ~PlmBaseCommand();

protected:
    PlmBridge* _bridge;
};

/** Login command - shows login dialog */
class PlmLoginCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmLoginCommand(PlmBridge* bridge);
    virtual ~PlmLoginCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

/** Search Parts command - shows parts list dialog */
class PlmSearchCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmSearchCommand(PlmBridge* bridge);
    virtual ~PlmSearchCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

/** Checkout command - downloads and opens part file */
class PlmCheckoutCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmCheckoutCommand(PlmBridge* bridge);
    virtual ~PlmCheckoutCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

/** Checkin command - uploads current document */
class PlmCheckinCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmCheckinCommand(PlmBridge* bridge);
    virtual ~PlmCheckinCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

/** Publish command - changes lifecycle state */
class PlmPublishCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmPublishCommand(PlmBridge* bridge);
    virtual ~PlmPublishCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

/** Sync Properties command - writes PLM attributes to CATIA document */
class PlmSyncCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmSyncCommand(PlmBridge* bridge);
    virtual ~PlmSyncCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

/** Create Part command - shows new part dialog */
class PlmCreatePartCommand : public PlmBaseCommand
{
    CATDeclareClass;

public:
    PlmCreatePartCommand(PlmBridge* bridge);
    virtual ~PlmCreatePartCommand();

    void Activate(CATCommand* iFromClient, CATNotification* iNotification);
};

#endif
