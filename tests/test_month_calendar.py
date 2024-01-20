from __future__ import annotations

import datetime

import pytest

from textual import on
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import DataTable, MonthCalendar
from textual.widgets.month_calendar import InvalidWeekdayNumber


def test_invalid_month_raises_exception():
    with pytest.raises(ValueError):
        _ = MonthCalendar(datetime.date(year=2021, month=13, day=3))


def test_invalid_day_raises_exception():
    with pytest.raises(ValueError):
        _ = MonthCalendar(datetime.date(year=2021, month=6, day=32))


def test_invalid_weekday_number_raises_exception():
    with pytest.raises(InvalidWeekdayNumber):
        _ = MonthCalendar(first_weekday=7)


def test_calendar_dates_property():
    month_calendar = MonthCalendar(datetime.date(year=2021, month=6, day=3))
    first_monday = datetime.date(2021, 5, 31)
    expected_date = first_monday
    for week in range(len(month_calendar._calendar_dates)):
        for day in range(0, 7):
            assert month_calendar._calendar_dates[week][day] == expected_date
            expected_date += datetime.timedelta(days=1)


def test_get_date_coordinate():
    month_calendar = MonthCalendar(datetime.date(year=2021, month=6, day=3))
    expected_coordinate = Coordinate(0, 3)
    actual_coordinate = month_calendar._get_date_coordinate(
        datetime.date(2021, 6, 3),
    )
    assert actual_coordinate == expected_coordinate


def test_get_date_coordinate_when_out_of_range():
    month_calendar = MonthCalendar(datetime.date(year=2021, month=6, day=3))
    with pytest.raises(ValueError):
        month_calendar._get_date_coordinate(datetime.date(2021, 1, 1))


async def test_calendar_defaults_to_today_if_no_date_provided():
    class TodayCalendarApp(App):
        def compose(self) -> ComposeResult:
            yield MonthCalendar()

    app = TodayCalendarApp()
    async with app.run_test() as pilot:
        today = datetime.date.today()
        month_calendar = pilot.app.query_one(MonthCalendar)
        assert month_calendar.date.month == today.month
        assert month_calendar.date.year == today.year

        table = month_calendar.query_one(DataTable)
        assert table.get_cell_at(table.cursor_coordinate).plain == str(today.day)


class MonthCalendarApp(App):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[tuple[str, datetime.date]] = []

    def compose(self) -> ComposeResult:
        yield MonthCalendar(datetime.date(year=2021, month=6, day=3))

    @on(MonthCalendar.DateHighlighted)
    @on(MonthCalendar.DateSelected)
    def record(
        self,
        event: MonthCalendar.DateHighlighted | MonthCalendar.DateSelected,
    ) -> None:
        self.messages.append((event.__class__.__name__, event.value))


async def test_calendar_table_week_header():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        actual_labels = [col.label.plain for col in table.columns.values()]
        expected_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        assert actual_labels == expected_labels


async def test_calendar_table_days():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        for row, week in enumerate(month_calendar._calendar_dates):
            for column, date in enumerate(week):
                actual_day = table.get_cell_at(Coordinate(row, column)).plain
                assert isinstance(date, datetime.date)
                expected_day = str(date.day)
                assert actual_day == expected_day


async def test_calendar_table_after_reactive_date_change_to_different_month():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.date = datetime.date(year=2022, month=10, day=2)

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2022, 9, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "26"

        assert table.get_cell_at(table.cursor_coordinate).plain == "2"


async def test_calendar_table_after_reactive_date_change_within_same_month():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.date = datetime.date(year=2021, month=6, day=19)

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2021, 5, 31)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "31"

        assert table.get_cell_at(table.cursor_coordinate).plain == "19"


async def test_calendar_table_after_reactive_first_weekday_change():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.first_weekday = 6  # Sunday
        table = month_calendar.query_one(DataTable)

        actual_labels = [col.label.plain for col in table.columns.values()]
        expected_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        assert actual_labels == expected_labels

        expected_first_sunday = datetime.date(2021, 5, 30)
        actual_first_sunday = month_calendar._calendar_dates[0][0]
        assert actual_first_sunday == expected_first_sunday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "30"

        assert table.get_cell_at(table.cursor_coordinate).plain == "3"


async def test_show_cursor():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        assert table.show_cursor is True
        month_calendar.show_cursor = False
        assert table.show_cursor is False


async def test_previous_year():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.previous_year()

        assert month_calendar.date.year == 2020
        assert month_calendar.date.month == 6

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2020, 5, 25)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "25"


async def test_next_year():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.next_year()

        assert month_calendar.date.year == 2022
        assert month_calendar.date.month == 6

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2022, 5, 30)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "30"


async def test_previous_month():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.previous_month()

        assert month_calendar.date.year == 2021
        assert month_calendar.date.month == 5

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2021, 4, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "26"


async def test_previous_month_when_month_is_january():
    class JanuaryCalendarApp(App):
        def compose(self) -> ComposeResult:
            yield MonthCalendar(datetime.date(year=2021, month=1, day=1))

    app = JanuaryCalendarApp()
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.previous_month()

        assert month_calendar.date.year == 2020
        assert month_calendar.date.month == 12

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2020, 11, 30)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "30"


async def test_next_month():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.next_month()

        assert month_calendar.date.year == 2021
        assert month_calendar.date.month == 7

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2021, 6, 28)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "28"


async def test_next_month_when_month_is_december():
    class DecemberCalendarApp(App):
        def compose(self) -> ComposeResult:
            yield MonthCalendar(datetime.date(year=2021, month=12, day=1))

    app = DecemberCalendarApp()
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.next_month()

        assert month_calendar.date.year == 2022
        assert month_calendar.date.month == 1

        table = month_calendar.query_one(DataTable)
        expected_first_monday = datetime.date(2021, 12, 27)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "27"


async def test_cell_highlighted_updates_date():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        await pilot.press("right")
        expected_date = datetime.date(2021, 6, 4)
        assert month_calendar.date == expected_date

        await pilot.press("down")
        expected_date = datetime.date(2021, 6, 11)
        assert month_calendar.date == expected_date

        await pilot.press("left")
        expected_date = datetime.date(2021, 6, 10)
        assert month_calendar.date == expected_date


async def test_hover_coordinate_persists_after_month_changes():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        await pilot.hover(MonthCalendar, offset=(3, 3))
        assert table.hover_coordinate == Coordinate(2, 0)

        month_calendar.date = datetime.date(year=2022, month=10, day=2)
        assert table.hover_coordinate == Coordinate(2, 0)


async def test_hover_coordinate_persists_after_first_weekday_changes():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        await pilot.hover(MonthCalendar, offset=(3, 3))
        assert table.hover_coordinate == Coordinate(2, 0)

        month_calendar.first_weekday = 6  # Sunday
        assert table.hover_coordinate == Coordinate(2, 0)


async def test_calendar_updates_if_date_outside_month_highlighted():
    """If `show_other_months` is True, highlighting a date from the previous
    or next month should update the calendar to bring that entire month into
    view"""

    class ShowOtherMonthsApp(App):
        def compose(self) -> ComposeResult:
            yield MonthCalendar(
                datetime.date(year=2021, month=6, day=1),
                show_other_months=True,
            )

    app = ShowOtherMonthsApp()
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        # Sanity check
        assert table.cursor_coordinate == Coordinate(0, 1)
        expected_first_monday = datetime.date(2021, 5, 31)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "31"

        await pilot.press("left")
        assert month_calendar.date == datetime.date(2021, 5, 31)
        assert table.cursor_coordinate == Coordinate(5, 0)
        expected_first_monday = datetime.date(2021, 4, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "26"


async def test_calendar_if_show_other_months_is_false():
    """If `show_other_months` is False, only dates from the current month
    should be displayed and other blank cells should not be selectable"""

    class HideOtherMonthsApp(App):
        def __init__(self) -> None:
            super().__init__()
            self.messages: list[tuple[str, datetime.date]] = []

        def compose(self) -> ComposeResult:
            yield MonthCalendar(
                datetime.date(year=2021, month=6, day=1),
                show_other_months=False,
            )

        @on(MonthCalendar.DateHighlighted)
        @on(MonthCalendar.DateSelected)
        def record(
            self,
            event: MonthCalendar.DateHighlighted | MonthCalendar.DateSelected,
        ) -> None:
            self.messages.append((event.__class__.__name__, event.value))

    app = HideOtherMonthsApp()
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)

        expected_messages = [("DateHighlighted", datetime.date(2021, 6, 1))]
        expected_coordinate = Coordinate(0, 1)
        expected_date = datetime.date(2021, 6, 1)
        # Sanity check
        expected_first_monday = None
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)) == expected_first_monday

        assert month_calendar.date == expected_date
        assert table.cursor_coordinate == expected_coordinate
        assert app.messages == expected_messages

        await pilot.press("left")
        assert table.cursor_coordinate == expected_coordinate
        assert app.messages == expected_messages
        assert month_calendar.date == expected_date

        await pilot.click(MonthCalendar, offset=(3, 1))
        assert table.cursor_coordinate == expected_coordinate
        assert app.messages == expected_messages
        assert month_calendar.date == expected_date

        await pilot.hover(MonthCalendar, offset=(3, 1))
        assert table._show_hover_cursor is False


async def test_calendar_after_reactive_show_other_months_change():
    class ShowOtherMonthsApp(App):
        def compose(self) -> ComposeResult:
            yield MonthCalendar(
                datetime.date(year=2021, month=6, day=1),
                show_other_months=True,
            )

    app = ShowOtherMonthsApp()
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        table = month_calendar.query_one(DataTable)
        # Sanity check
        expected_first_monday = datetime.date(2021, 5, 31)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)).plain == "31"

        month_calendar.show_other_months = False
        expected_first_monday = None
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert table.get_cell_at(Coordinate(0, 0)) is None


async def test_clicking_data_table_cell_emits_highlighted_before_selected_message():
    """It is important for the `MonthCalendar` that the table will emit a
    `CellHighlighted` message *before* `CellSelected` when a cell is clicked.
    This means it is safe to simply use the `date` for the `DateSelected`
    message. We cannot rely on the `event.coordinate` for the selected date,
    as selecting a date from the previous or next month will update the calendar
    to bring that entire month into view and the date at this co-ordinate will
    have changed!
    """

    class DataTableApp(App):
        def __init__(self) -> None:
            super().__init__()
            self.messages: list[tuple[str, str]] = []

        def compose(self) -> ComposeResult:
            yield DataTable()

        def on_mount(self) -> None:
            table = self.query_one(DataTable)
            with self.prevent(DataTable.CellHighlighted):
                table.add_columns("Col0", "Col1")
                table.add_row(*["0/0", "0/1"])

        @on(DataTable.CellHighlighted)
        @on(DataTable.CellSelected)
        def record(
            self, event: DataTable.CellHighlighted | DataTable.CellSelected
        ) -> None:
            self.messages.append((event.__class__.__name__, str(event.value)))

    app = DataTableApp()
    async with app.run_test() as pilot:
        await pilot.click(DataTable, offset=(8, 1))
        assert app.messages == [
            ("CellHighlighted", "0/1"),
            ("CellSelected", "0/1"),
        ]


async def test_month_calendar_message_emission():
    app = MonthCalendarApp()  # MonthCalendar date is 2021-06-03
    expected_messages = []
    async with app.run_test() as pilot:
        expected_messages.append(("DateHighlighted", datetime.date(2021, 6, 3)))
        assert app.messages == expected_messages

        await pilot.press("enter")
        expected_messages.append(("DateSelected", datetime.date(2021, 6, 3)))
        assert app.messages == expected_messages

        await pilot.press("right")
        expected_messages.append(("DateHighlighted", datetime.date(2021, 6, 4)))
        assert app.messages == expected_messages

        await pilot.click(MonthCalendar, offset=(2, 1))
        expected_messages.append(("DateHighlighted", datetime.date(2021, 5, 31)))
        expected_messages.append(("DateSelected", datetime.date(2021, 5, 31)))
        # TODO: This probably shouldn't emit another DateHighlighted message?
        expected_messages.append(("DateHighlighted", datetime.date(2021, 5, 31)))
        assert app.messages == expected_messages

        month_calendar = pilot.app.query_one(MonthCalendar)
        month_calendar.previous_month()
        await pilot.pause()
        expected_messages.append(("DateHighlighted", datetime.date(2021, 4, 30)))
        assert app.messages == expected_messages
