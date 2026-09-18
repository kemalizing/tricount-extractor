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


def test_transaction_ledger_with_expense_reimbursement_income_and_nonparticipant():
    """Test transaction_ledger sheet with expense, reimbursement, income, and a member not in allocations."""
    members = [
        Member(id=1, uuid="user-a", display_name="Alice", status="ACTIVE"),
        Member(id=2, uuid="user-b", display_name="Bob", status="ACTIVE"),
        Member(id=3, uuid="user-c", display_name="Charlie", status="ACTIVE"),
    ]

    entries = [
        # Expense: Alice pays $30, split between Alice and Bob (Charlie not involved)
        Entry(
            id=1,
            uuid="entry-001",
            created=datetime.datetime(2025, 1, 1, 10, 0),
            date=datetime.datetime(2025, 1, 1, 10, 0),
            description="Groceries",
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
        # Reimbursement: Bob reimburses Alice $10
        Entry(
            id=2,
            uuid="entry-002",
            created=datetime.datetime(2025, 1, 2, 12, 0),
            date=datetime.datetime(2025, 1, 2, 12, 0),
            description="Bob reimburses Alice",
            amount=Amount(currency="USD", value=10.0),
            amount_local=Amount(currency="USD", value=10.0),
            status="ACTIVE",
            type=EntryType.MANUAL,
            type_transaction=EntryTypeTransaction.BALANCE,
            payer_uuid="user-b",
            payer_name="Bob",
            category="BALANCE",
            allocations=[
                Allocation(
                    member_uuid="user-a",
                    member_name="Alice",
                    amount=Amount(currency="USD", value=10.0),
                    amount_local=Amount(currency="USD", value=10.0),
                    type="RATIO",
                    share_ratio=1,
                ),
            ],
        ),
        # Income: Charlie receives $50, split among all three
        Entry(
            id=3,
            uuid="entry-003",
            created=datetime.datetime(2025, 1, 3, 14, 0),
            date=datetime.datetime(2025, 1, 3, 14, 0),
            description="Prize money",
            amount=Amount(currency="USD", value=50.0),
            amount_local=Amount(currency="USD", value=50.0),
            status="ACTIVE",
            type=EntryType.MANUAL,
            type_transaction=EntryTypeTransaction.INCOME,
            payer_uuid="user-c",
            payer_name="Charlie",
            category="INCOME",
            allocations=[
                Allocation(
                    member_uuid="user-a",
                    member_name="Alice",
                    amount=Amount(currency="USD", value=16.67),
                    amount_local=Amount(currency="USD", value=16.67),
                    type="RATIO",
                    share_ratio=1,
                ),
                Allocation(
                    member_uuid="user-b",
                    member_name="Bob",
                    amount=Amount(currency="USD", value=16.67),
                    amount_local=Amount(currency="USD", value=16.67),
                    type="RATIO",
                    share_ratio=1,
                ),
                Allocation(
                    member_uuid="user-c",
                    member_name="Charlie",
                    amount=Amount(currency="USD", value=16.66),
                    amount_local=Amount(currency="USD", value=16.66),
                    type="RATIO",
                    share_ratio=1,
                ),
            ],
        ),
    ]

    registry = Registry(
        id=1,
        uuid="reg-001",
        title="Test Trip",
        currency="USD",
        created=datetime.datetime(2025, 1, 1),
        updated=datetime.datetime(2025, 1, 3),
        members=members,
        entries=entries,
        pagination=Pagination(future_url=None, newer_url=None, older_url=None),
    )

    ledger_df = registry._to_transaction_ledger_dataframe()

    # Check shape and columns
    assert len(ledger_df) == 3
    assert "date" in ledger_df.columns
    assert "description" in ledger_df.columns
    assert "category" in ledger_df.columns
    assert "type" in ledger_df.columns
    assert "cost" in ledger_df.columns
    assert "currency" in ledger_df.columns
    assert "Alice" in ledger_df.columns
    assert "Bob" in ledger_df.columns
    assert "Charlie" in ledger_df.columns

    # Check entry 1 (Expense): Alice pays $30, split between Alice and Bob
    # Alice: owes -$15, paid -$30 -> net = -15 - (-30) = 15 (she is owed $15)
    # Bob: owes -$15, paid $0 -> net = -15 - 0 = -15 (he owes $15)
    # Charlie: owes $0, paid $0 -> net = 0 - 0 = 0 (not involved)
    row1 = ledger_df.iloc[0]
    assert row1["date"] == "2025-01-01"
    assert row1["description"] == "Groceries"
    assert row1["category"] == "FOOD"
    assert row1["type"] == "Expense"
    assert row1["cost"] == -30.0
    assert row1["currency"] == "USD"
    assert row1["Alice"] == 15.0
    assert row1["Bob"] == -15.0
    assert row1["Charlie"] == 0.0

    # Check entry 2 (Reimbursement): Bob reimburses Alice $10
    # Alice: owes $10, paid $0 -> net = 10 - 0 = 10 (she receives $10)
    # Bob: owes $0, paid $10 -> net = 0 - 10 = -10 (he pays $10)
    # Charlie: owes $0, paid $0 -> net = 0 - 0 = 0 (not involved)
    # Cost should be 0 for reimbursements
    row2 = ledger_df.iloc[1]
    assert row2["date"] == "2025-01-02"
    assert row2["description"] == "Bob reimburses Alice"
    assert row2["category"] == "BALANCE"
    assert row2["type"] == "Transfer"
    assert row2["cost"] == 0.0
    assert row2["currency"] == "USD"
    assert row2["Alice"] == 10.0
    assert row2["Bob"] == -10.0
    assert row2["Charlie"] == 0.0

    # Check entry 3 (Income): Charlie receives $50, split among all three
    # Alice: owes $16.67, paid $0 -> net = 16.67 - 0 = 16.67 (she owes $16.67)
    # Bob: owes $16.67, paid $0 -> net = 16.67 - 0 = 16.67 (he owes $16.67)
    # Charlie: owes $16.66, paid $50 -> net = 16.66 - 50 = -33.34 (he is owed $33.34)
    row3 = ledger_df.iloc[2]
    assert row3["date"] == "2025-01-03"
    assert row3["description"] == "Prize money"
    assert row3["category"] == "INCOME"
    assert row3["type"] == "Income"
    assert row3["cost"] == 50.0
    assert row3["currency"] == "USD"
    assert row3["Alice"] == 16.67
    assert row3["Bob"] == 16.67
    assert row3["Charlie"] == -33.34
