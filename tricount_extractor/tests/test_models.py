import datetime
import pytest

from tricount_extractor.models.allocation import Allocation
from tricount_extractor.models.amount import Amount
from tricount_extractor.models.entry import Entry, EntryType, EntryTypeTransaction
from tricount_extractor.models.member import Member
from tricount_extractor.models.pagination import Pagination
from tricount_extractor.models.registry import Registry


@pytest.fixture
def sample_members():
    return [
        Member(
            id=1,
            uuid="user-a",
            display_name="Alice",
            status="ACTIVE",
        ),
        Member(
            id=2,
            uuid="user-b",
            display_name="Bob",
            status="ACTIVE",
        ),
    ]


def test_balance_preserves_sign_for_expenses(sample_members):
    """Test that balance calculation correctly handles negative expense amounts."""
    # Alice pays $20 expense, split equally between Alice and Bob
    entry = Entry(
        id=1,
        uuid="entry-001",
        created=datetime.datetime(2025, 1, 1),
        date=datetime.datetime(2025, 1, 1),
        description="Lunch",
        amount=Amount(currency="USD", value=-20.0),
        amount_local=Amount(currency="USD", value=-20.0),
        status="ACTIVE",
        type=EntryType.MANUAL,
        type_transaction=EntryTypeTransaction.NORMAL,
        payer_uuid="user-a",
        payer_name="Alice",
        category="FOOD",
        allocations=[
            Allocation(
                member_uuid="user-a",
                member_name="Alice",
                amount=Amount(currency="USD", value=-10.0),
                amount_local=Amount(currency="USD", value=-10.0),
                type="RATIO",
                share_ratio=1,
            ),
            Allocation(
                member_uuid="user-b",
                member_name="Bob",
                amount=Amount(currency="USD", value=-10.0),
                amount_local=Amount(currency="USD", value=-10.0),
                type="RATIO",
                share_ratio=1,
            ),
        ],
    )

    registry = Registry(
        id=1,
        uuid="reg-001",
        title="Test",
        currency="USD",
        created=datetime.datetime(2025, 1, 1),
        updated=datetime.datetime(2025, 1, 1),
        members=sample_members,
        entries=[entry],
        pagination=Pagination(future_url=None, newer_url=None, older_url=None),
    )

    balance_df = registry._to_balance_dataframe()

    # Alice paid $20 and owes $10, net = -20 + 10 = -10 (she is owed $10)
    # Bob paid $0 and owes $10, net = 0 + 10 = -10 (he owes $10)
    alice_balance = balance_df[balance_df["member"] == "Alice"]["balance"].values[0]
    bob_balance = balance_df[balance_df["member"] == "Bob"]["balance"].values[0]

    assert alice_balance == -10.0
    assert bob_balance == 10.0


def test_balance_preserves_sign_for_income(sample_members):
    """Test that balance calculation correctly handles positive income amounts."""
    # Alice receives $100 income, split equally between Alice and Bob
    entry = Entry(
        id=2,
        uuid="entry-002",
        created=datetime.datetime(2025, 1, 2),
        date=datetime.datetime(2025, 1, 2),
        description="Refund",
        amount=Amount(currency="USD", value=100.0),
        amount_local=Amount(currency="USD", value=100.0),
        status="ACTIVE",
        type=EntryType.MANUAL,
        type_transaction=EntryTypeTransaction.INCOME,
        payer_uuid="user-a",
        payer_name="Alice",
        category="INCOME",
        allocations=[
            Allocation(
                member_uuid="user-a",
                member_name="Alice",
                amount=Amount(currency="USD", value=50.0),
                amount_local=Amount(currency="USD", value=50.0),
                type="RATIO",
                share_ratio=1,
            ),
            Allocation(
                member_uuid="user-b",
                member_name="Bob",
                amount=Amount(currency="USD", value=50.0),
                amount_local=Amount(currency="USD", value=50.0),
                type="RATIO",
                share_ratio=1,
            ),
        ],
    )

    registry = Registry(
        id=1,
        uuid="reg-001",
        title="Test",
        currency="USD",
        created=datetime.datetime(2025, 1, 1),
        updated=datetime.datetime(2025, 1, 1),
        members=sample_members,
        entries=[entry],
        pagination=Pagination(future_url=None, newer_url=None, older_url=None),
    )

    balance_df = registry._to_balance_dataframe()

    # Alice received $100 and is allocated $50, net = 100 - 50 = 50 (she owes $50)
    # Bob received $0 and is allocated $50, net = 0 - 50 = -50 (he is owed $50)
    alice_balance = balance_df[balance_df["member"] == "Alice"]["balance"].values[0]
    bob_balance = balance_df[balance_df["member"] == "Bob"]["balance"].values[0]

    assert alice_balance == 50.0
    assert bob_balance == -50.0


def test_balance_with_mixed_transactions(sample_members):
    """Test that balance calculation correctly handles a mix of expenses and income."""
    entries = [
        # Alice pays $30 expense, split equally
        Entry(
            id=1,
            uuid="entry-001",
            created=datetime.datetime(2025, 1, 1),
            date=datetime.datetime(2025, 1, 1),
            description="Dinner",
            amount=Amount(currency="USD", value=-30.0),
            amount_local=Amount(currency="USD", value=-30.0),
            status="ACTIVE",
            type=EntryType.MANUAL,
            type_transaction=EntryTypeTransaction.NORMAL,
            payer_uuid="user-a",
            payer_name="Alice",
            category="FOOD",
            allocations=[
                Allocation(
                    member_uuid="user-a",
                    member_name="Alice",
                    amount=Amount(currency="USD", value=-15.0),
                    amount_local=Amount(currency="USD", value=-15.0),
                    type="RATIO",
                    share_ratio=1,
                ),
                Allocation(
                    member_uuid="user-b",
                    member_name="Bob",
                    amount=Amount(currency="USD", value=-15.0),
                    amount_local=Amount(currency="USD", value=-15.0),
                    type="RATIO",
                    share_ratio=1,
                ),
            ],
        ),
        # Bob receives $20 income, split equally
        Entry(
            id=2,
            uuid="entry-002",
            created=datetime.datetime(2025, 1, 2),
            date=datetime.datetime(2025, 1, 2),
            description="Cash back",
            amount=Amount(currency="USD", value=20.0),
            amount_local=Amount(currency="USD", value=20.0),
            status="ACTIVE",
            type=EntryType.MANUAL,
            type_transaction=EntryTypeTransaction.INCOME,
            payer_uuid="user-b",
            payer_name="Bob",
            category="INCOME",
            allocations=[
                Allocation(
                    member_uuid="user-a",
                    member_name="Alice",
                    amount=Amount(currency="USD", value=10.0),
                    amount_local=Amount(currency="USD", value=10.0),
                    type="RATIO",
                    share_ratio=1,
                ),
                Allocation(
                    member_uuid="user-b",
                    member_name="Bob",
                    amount=Amount(currency="USD", value=10.0),
                    amount_local=Amount(currency="USD", value=10.0),
                    type="RATIO",
                    share_ratio=1,
                ),
            ],
        ),
    ]

    registry = Registry(
        id=1,
        uuid="reg-001",
        title="Test",
        currency="USD",
        created=datetime.datetime(2025, 1, 1),
        updated=datetime.datetime(2025, 1, 1),
        members=sample_members,
        entries=entries,
        pagination=Pagination(future_url=None, newer_url=None, older_url=None),
    )

    balance_df = registry._to_balance_dataframe()

    # Alice: paid $30 (expense), owes $15, allocated $10 (income)
    # Net = -30 + 15 - 10 = -25 (she is owed $25)
    # Bob: paid $0 (expense), owes $15, received $20 (income), allocated $10
    # Net = 0 + 15 + 20 - 10 = 25 (he owes $25)
    alice_balance = balance_df[balance_df["member"] == "Alice"]["balance"].values[0]
    bob_balance = balance_df[balance_df["member"] == "Bob"]["balance"].values[0]

    assert alice_balance == -25.0
    assert bob_balance == 25.0
    # Balances should sum to zero
    assert balance_df["balance"].sum() == 0.0
