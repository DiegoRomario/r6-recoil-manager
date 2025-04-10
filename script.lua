--#region keys
EnableScriptKey = "NUMLOCK" -- Turns Script ON/OFF
EnableAutoClickKey = "SCROLLLOCK" -- Turns Script ON/OFF
LeftClick = 1 -- 1 = Left | 2 = Middle | 3 = Right | 4 = Side (2)
RightClick = 3
SideClick = 4
--#endregion

HorizontalRecoilCompensation = 0
VerticalRecoilCompensation = 0
MouseMoveDelay = 8 -- Delay in miliseconds between each time RecoilMouseMoveAmount More==less mouse pull down, 1 mousemove==100 DelaySleep

AutoClickDelayBetweenShots = 8 -- Delay in (roughly) miliseconds  between each time SMG/AR/RecoilMouseMoveAmount moves your mouse  
AutoClickRecoilCompensation = 10 -- In between each auto clik shot, it will pull the mouse down More == Pulling the Mouse down more between shots
AutoClickMousePressDurationAR = 1 -- How long is left click held for auto click in milliseconds. 1 == 1 tap
  
AutoClickSleepMin = 0
AutoClickSleepMax = 0

SleepNoRecoilMin = MouseMoveDelay - 1
SleepNoRecoilMax = MouseMoveDelay + 1

EnablePrimaryMouseButtonEvents(true);

function AutoClick()
    if (AutoClickDelayBetweenShots > 10) then
        AutoClickSleepMin = AutoClickDelayBetweenShots - 5
        AutoClickSleepMin = AutoClickDelayBetweenShots - AutoClickDelayBetweenShots + 5
        AutoClickSleepMax = AutoClickDelayBetweenShots + 5
    end

    if (AutoClickMousePressDurationAR > 1) then
        PressSpeedMin = AutoClickMousePressDurationAR - 1
        PressSpeedMax = AutoClickMousePressDurationAR + 1
    else
        PressSpeedMin = AutoClickMousePressDurationAR
        PressSpeedMax = AutoClickMousePressDurationAR + 1
    end

    repeat
        PressMouseButton(LeftClick)
        Sleep(math.random(PressSpeedMin, PressSpeedMax))
        ReleaseMouseButton(LeftClick)
        Sleep(math.random(PressSpeedMin, PressSpeedMax))
        MoveMouseRelative(HorizontalRecoilCompensation, AutoClickRecoilCompensation)
        Sleep(math.random(AutoClickSleepMin, AutoClickSleepMax))
    until not IsMouseButtonPressed(RightClick)
end

function NoRecoil()
    repeat
        MoveMouseRelative(HorizontalRecoilCompensation, VerticalRecoilCompensation)
        Sleep(math.random(SleepNoRecoilMin, SleepNoRecoilMax))
    until not IsMouseButtonPressed(LeftClick)
end

function OnEvent()
    if IsKeyLockOn(EnableScriptKey) then
        if (IsMouseButtonPressed(RightClick)) then
            repeat
                if IsMouseButtonPressed(LeftClick) then
                    NoRecoil()
                elseif IsMouseButtonPressed(SideClick) and IsKeyLockOn(EnableAutoClickKey) then
                    AutoClick()
                end
            until not IsMouseButtonPressed(RightClick)
        end
    end
end